"""Testes de integração para os endpoints de Demonstração e Auditoria (`/api/v1/demo/*`)."""

from httpx import AsyncClient


async def test_demo_seed_comparison_inspect_tamper_and_playground(
    client: AsyncClient,
) -> None:
    """Valida todos os endpoints de demonstração criptográfica."""
    # 1. Healthcheck
    health = await client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    # 2. Seed & Compare (2 pacientes com 80.0 kg e mesmos dados médicos)
    seed_resp = await client.post("/api/v1/demo/seed-comparison")
    assert seed_resp.status_code == 200
    seed_data = seed_resp.json()
    assert seed_data["derived_keys_are_different"] is True
    assert seed_data["same_password_comparison"]["hashes_are_different"] is True
    for item in seed_data["identical_medical_fields_comparison"]:
        assert item["ciphertexts_are_different"] is True

    # 3. Inspect User Crypto (visão banco vs visão API)
    user_a_id = seed_data["user_a_id"]
    inspect_resp = await client.get(f"/api/v1/demo/inspect-user/{user_a_id}")
    assert inspect_resp.status_code == 200
    inspect_data = inspect_resp.json()
    assert inspect_data["medical_fields"]["weight_kg"]["plaintext_value"] == 80.0
    assert inspect_data["medical_fields"]["weight_kg"]["raw_database_value"].startswith("v1$")

    # 4. Tamper Check (prova que copiar ciphertext entre usuários ou colunas falha)
    tamper_resp = await client.post("/api/v1/demo/tamper-check")
    assert tamper_resp.status_code == 200
    tamper_data = tamper_resp.json()
    assert tamper_data["all_attacks_blocked"] is True
    assert len(tamper_data["scenarios"]) == 3

    # 5. Crypto Playground interativo
    playground_resp = await client.post(
        "/api/v1/demo/crypto-playground",
        json={
            "sample_plaintext": "80.0",
            "field_name": "weight_kg",
            "sample_password": "SenhaForte@123",
        },
    )
    assert playground_resp.status_code == 200
    assertions = playground_resp.json()["proof_assertions"]
    assert assertions["user_1_and_user_2_ciphertexts_differ"] is True
    assert assertions["same_user_two_writes_ciphertexts_differ"] is True
    assert assertions["both_decrypt_to_exact_input"] is True
    assert assertions["password_hashes_differ"] is True
    assert assertions["blind_indexes_match_for_equality_search"] is True
