import importlib
import shutil
from pathlib import Path

from app.core import crypto as crypto_module
from app.core.crypto import sign_payload, verify_signature


def test_keypair_persists_across_simulated_restart(tmp_path, monkeypatch):
    """The core Phase 5 claim: a keypair generated on 'first run' must
    be reused (not regenerated) on a subsequent run, and a certificate
    signed before the 'restart' must still verify after it — proving
    the exact failure mode from earlier phases (ephemeral key
    invalidating everything on restart) is now fixed by default,
    without requiring anyone to manually set env vars.
    """
    # Point the module at a throwaway keys/ location for this test
    fake_backend_root = tmp_path / "backend_root"
    (fake_backend_root / "app" / "core").mkdir(parents=True)
    monkeypatch.setattr(
        crypto_module, "__file__",
        str(fake_backend_root / "app" / "core" / "crypto.py"),
    )
    # Ensure no env-var override interferes with this test
    crypto_module.settings.SIGNING_PRIVATE_KEY_PEM = None
    crypto_module.settings.SIGNING_PUBLIC_KEY_PEM = None

    # "First run": generates and persists a keypair
    private1, public1 = crypto_module.get_or_create_dev_keypair()
    keys_dir = fake_backend_root / "keys"
    assert (keys_dir / "private.pem").exists()
    assert (keys_dir / "public.pem").exists()

    payload = {"target_description": "SN-PERSIST-TEST"}
    report_hash, signature = sign_payload(payload, private1)
    assert verify_signature(payload, signature, public1) is True

    # "Restart": call again as if the process just started fresh —
    # must load the SAME key from disk, not generate a new one.
    private2, public2 = crypto_module.get_or_create_dev_keypair()
    assert private2 == private1
    assert public2 == public1

    # The certificate signed "before the restart" must still verify
    # "after" it, using whatever key get_or_create_dev_keypair now returns.
    assert verify_signature(payload, signature, public2) is True


def test_env_var_keys_take_priority_over_persisted_file(tmp_path, monkeypatch):
    """If real env vars are set (the production path), they must win
    even if a keys/ directory happens to exist — env vars are the
    explicit, authoritative source."""
    from app.core.crypto import generate_keypair

    fake_backend_root = tmp_path / "backend_root"
    (fake_backend_root / "app" / "core").mkdir(parents=True)
    monkeypatch.setattr(
        crypto_module, "__file__",
        str(fake_backend_root / "app" / "core" / "crypto.py"),
    )

    file_priv, file_pub = generate_keypair()
    keys_dir = fake_backend_root / "keys"
    keys_dir.mkdir(parents=True)
    (keys_dir / "private.pem").write_text(file_priv)
    (keys_dir / "public.pem").write_text(file_pub)

    env_priv, env_pub = generate_keypair()
    crypto_module.settings.SIGNING_PRIVATE_KEY_PEM = env_priv
    crypto_module.settings.SIGNING_PUBLIC_KEY_PEM = env_pub

    resolved_priv, resolved_pub = crypto_module.get_or_create_dev_keypair()
    assert resolved_priv == env_priv
    assert resolved_pub == env_pub
    assert resolved_priv != file_priv

    # cleanup so this doesn't leak into other tests
    crypto_module.settings.SIGNING_PRIVATE_KEY_PEM = None
    crypto_module.settings.SIGNING_PUBLIC_KEY_PEM = None
