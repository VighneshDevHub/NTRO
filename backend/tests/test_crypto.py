from app.core.crypto import generate_keypair, sign_payload, verify_signature


def test_sign_and_verify_roundtrip():
    private_pem, public_pem = generate_keypair()
    payload = {"target_description": "SN-ABC123", "success": True}

    report_hash, signature = sign_payload(payload, private_pem)

    assert len(report_hash) == 64
    assert verify_signature(payload, signature, public_pem) is True


def test_verify_fails_if_payload_altered_after_signing():
    private_pem, public_pem = generate_keypair()
    payload = {"target_description": "SN-ABC123", "success": True}

    _hash, signature = sign_payload(payload, private_pem)

    tampered = {"target_description": "SN-ABC123", "success": False}
    assert verify_signature(tampered, signature, public_pem) is False


def test_verify_fails_with_wrong_public_key():
    private_pem, _public_pem = generate_keypair()
    _other_private, other_public_pem = generate_keypair()
    payload = {"target_description": "SN-ABC123"}

    _hash, signature = sign_payload(payload, private_pem)
    assert verify_signature(payload, signature, other_public_pem) is False
