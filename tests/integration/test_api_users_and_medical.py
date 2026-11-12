"""Testes de integração para CRUD de Usuários, Prontuários Médicos, Blind Index e Autenticação."""

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.user import User


async def test_create_two_users_with_identical_80kg_medical_data_stores_different_ciphertexts(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Prova no banco real que dois usuários com 80.0 kg e sangue O+ têm ciphertexts diferentes."""
    shared_medical = {
        "weight_kg": 80.0,
        "height_m": 1.75,
        "blood_type": "O+",
        "allergies": ["Dipirona"],
        "diagnoses": ["Hipertensão"],
        "medical_notes": "Paciente com 80 kg exatos.",
    }

    resp_a = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Paciente Um",
            "email": "paciente1@example.com",
            "cpf": "111.222.333-44",
            "password": "MesmaSenhaForte!123",
            "medical_record": shared_medical,
        },
    )
    assert resp_a.status_code == 201
    data_a = resp_a.json()

    resp_b = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Paciente Dois",
            "email": "paciente2@example.com",
            "cpf": "555.666.777-88",
            "password": "MesmaSenhaForte!123",
            "medical_record": shared_medical,
        },
    )
    assert resp_b.status_code == 201
    data_b = resp_b.json()

    # A API descriptografa ambos retornando exatamente 80.0 kg e IMC 26.12
    assert data_a["medical_record"]["weight_kg"] == 80.0
    assert data_b["medical_record"]["weight_kg"] == 80.0
    assert data_a["medical_record"]["bmi"] == 26.12

    # Inspecionando diretamente as linhas salvas no banco via SQLAlchemy:
    db_user_a = (await db_session.execute(select(User).where(User.id == data_a["id"]))).scalar_one()
    db_user_b = (await db_session.execute(select(User).where(User.id == data_b["id"]))).scalar_one()
    db_rec_a = (
        await db_session.execute(select(MedicalRecord).where(MedicalRecord.user_id == data_a["id"]))
    ).scalar_one()
    db_rec_b = (
        await db_session.execute(select(MedicalRecord).where(MedicalRecord.user_id == data_b["id"]))
    ).scalar_one()

    # Nenhum texto plano '80' ou 'Dipirona' aparece nas colunas criptografadas
    assert "80" not in db_rec_a.weight_kg_encrypted
    assert "Dipirona" not in db_rec_a.allergies_encrypted

    # Mesmo tendo exatamente os mesmos valores (80.0 kg, 1.75 m, O+, mesma senha), tudo no banco é diferente!
    assert db_user_a.user_salt != db_user_b.user_salt
    assert db_user_a.password_hash != db_user_b.password_hash
    assert db_rec_a.weight_kg_encrypted != db_rec_b.weight_kg_encrypted
    assert db_rec_a.height_m_encrypted != db_rec_b.height_m_encrypted
    assert db_rec_a.blood_type_encrypted != db_rec_b.blood_type_encrypted
    assert db_rec_a.allergies_encrypted != db_rec_b.allergies_encrypted
    assert db_rec_a.diagnoses_encrypted != db_rec_b.diagnoses_encrypted
    assert db_rec_a.medical_notes_encrypted != db_rec_b.medical_notes_encrypted


async def test_blind_index_search_by_cpf_email_and_blood_type_and_jwt_flow(
    client: AsyncClient,
) -> None:
    """Testa buscas O(1) por Blind Index (CPF, Email, Tipo Sanguíneo), atualização e Login JWT."""
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Carlos Silva",
            "email": "carlos.silva@example.com",
            "cpf": "123.456.789-01",
            "password": "CarlosPassword@123",
            "medical_record": {
                "weight_kg": 75.5,
                "height_m": 1.80,
                "blood_type": "AB-",
                "allergies": [],
                "diagnoses": ["Asma leve"],
                "medical_notes": "Controle anual.",
            },
        },
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    # Busca por CPF via Blind Index (mesmo enviando sem pontuação)
    cpf_search = await client.get("/api/v1/users/search/by-cpf", params={"cpf": "12345678901"})
    assert cpf_search.status_code == 200
    assert cpf_search.json()["id"] == user_id
    assert cpf_search.json()["full_name"] == "Carlos Silva"

    # Busca por E-mail via Blind Index (case-insensitive)
    email_search = await client.get(
        "/api/v1/users/search/by-email",
        params={"email": "CARLOS.SILVA@EXAMPLE.COM"},
    )
    assert email_search.status_code == 200
    assert email_search.json()["id"] == user_id

    # Busca de prontuários por tipo sanguíneo via Blind Index
    bt_search = await client.get(
        "/api/v1/medical-records/search/by-blood-type",
        params={"blood_type": "AB-"},
    )
    assert bt_search.status_code == 200
    assert len(bt_search.json()) == 1
    assert bt_search.json()[0]["user_id"] == user_id

    # Atualização parcial (PATCH) do peso para 80.0 kg
    patch_resp = await client.patch(
        f"/api/v1/medical-records/user/{user_id}",
        json={"weight_kg": 80.0},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["weight_kg"] == 80.0

    # Login JWT e consulta ao endpoint autenticado /auth/me
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "carlos.silva@example.com", "password": "CarlosPassword@123"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == user_id
    assert me_resp.json()["medical_record"]["weight_kg"] == 80.0

    # Verificação didática de senha (/auth/verify-password)
    verify_resp = await client.post(
        "/api/v1/auth/verify-password",
        json={"email": "carlos.silva@example.com", "password": "CarlosPassword@123"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["matched"] is True
    assert verify_resp.json()["algorithm"] == "argon2id"

    # Listagem, busca por ID, obtenção de prontuário e conflito de duplicidade (409)
    list_resp = await client.get("/api/v1/users")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    get_user_resp = await client.get(f"/api/v1/users/{user_id}")
    assert get_user_resp.status_code == 200

    get_med_resp = await client.get(f"/api/v1/medical-records/user/{user_id}")
    assert get_med_resp.status_code == 200
    assert get_med_resp.json()["weight_kg"] == 80.0

    dup_resp = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Outro Carlos",
            "email": "carlos.silva@example.com",
            "cpf": "999.888.777-66",
            "password": "CarlosPassword@123",
        },
    )
    assert dup_resp.status_code == 409

    del_resp = await client.delete(f"/api/v1/users/{user_id}")
    assert del_resp.status_code == 204

    not_found_resp = await client.get(f"/api/v1/users/{user_id}")
    assert not_found_resp.status_code == 404
