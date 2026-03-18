import sqlite3
import pytest
from api.signing import (
    init_signing_db, register_key, revoke_key, get_key, get_author_keys,
    sign_listing, verify_listing, get_signature_info,
    hash_manifest, canonical_json, compute_fingerprint,
)
from api.db import init_db


@pytest.fixture
def db_path(tmp_path):
    path = tmp_path / "test.db"
    init_db(path)
    init_signing_db(path)
    return path


class TestSigningDB:
    def test_init_creates_tables(self, db_path):
        conn = sqlite3.connect(db_path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = {t[0] for t in tables}
        assert "signing_keys" in table_names
        assert "listing_signatures" in table_names
        conn.close()

    def test_register_key(self, db_path):
        result = register_key(db_path, "key-1", "Alice", "base64pubkey==")
        assert result["registered"] is True
        assert "fingerprint" in result

    def test_register_duplicate_key(self, db_path):
        register_key(db_path, "key-1", "Alice", "base64pubkey==")
        result = register_key(db_path, "key-1", "Alice", "base64pubkey==")
        assert result["registered"] is False

    def test_get_key(self, db_path):
        register_key(db_path, "key-1", "Alice", "mypubkey")
        key = get_key(db_path, "key-1")
        assert key is not None
        assert key["author"] == "Alice"
        assert key["revoked_at"] is None

    def test_get_key_not_found(self, db_path):
        assert get_key(db_path, "nonexistent") is None

    def test_revoke_key(self, db_path):
        register_key(db_path, "key-1", "Alice", "mypubkey")
        result = revoke_key(db_path, "key-1")
        assert result["revoked"] is True
        key = get_key(db_path, "key-1")
        assert key["revoked_at"] is not None

    def test_revoke_nonexistent(self, db_path):
        result = revoke_key(db_path, "nonexistent")
        assert result["revoked"] is False

    def test_get_author_keys(self, db_path):
        register_key(db_path, "k1", "Alice", "pub1")
        register_key(db_path, "k2", "Alice", "pub2")
        register_key(db_path, "k3", "Bob", "pub3")
        keys = get_author_keys(db_path, "Alice")
        assert len(keys) == 2


class TestManifestHashing:
    def test_canonical_json_deterministic(self):
        d1 = {"b": 2, "a": 1}
        d2 = {"a": 1, "b": 2}
        assert canonical_json(d1) == canonical_json(d2)

    def test_hash_manifest(self):
        h = hash_manifest({"id": "test", "version": "1.0.0"})
        assert len(h) == 64  # SHA-256 hex

    def test_fingerprint(self):
        fp = compute_fingerprint("mypubkey")
        assert len(fp) == 16


class TestSignAndVerify:
    def test_sign_and_verify(self, db_path):
        register_key(db_path, "key-1", "Alice", "pubkey")
        manifest = {"id": "test", "title": "Test", "version": "1.0.0"}
        result = sign_listing(db_path, "test", "key-1", "fakesig==", manifest)
        assert result["signed"] is True

        verify = verify_listing(db_path, "test", manifest)
        assert verify["verified"] is True
        assert verify["status"] == "verified"

    def test_verify_unsigned(self, db_path):
        verify = verify_listing(db_path, "unsigned-listing", {"id": "test"})
        assert verify["verified"] is False
        assert verify["status"] == "unsigned"

    def test_verify_tampered(self, db_path):
        register_key(db_path, "key-1", "Alice", "pubkey")
        manifest = {"id": "test", "title": "Original"}
        sign_listing(db_path, "test", "key-1", "sig", manifest)
        tampered = {"id": "test", "title": "Tampered"}
        verify = verify_listing(db_path, "test", tampered)
        assert verify["verified"] is False
        assert verify["status"] == "tampered"

    def test_verify_revoked_key(self, db_path):
        register_key(db_path, "key-1", "Alice", "pubkey")
        manifest = {"id": "test", "title": "Test"}
        sign_listing(db_path, "test", "key-1", "sig", manifest)
        revoke_key(db_path, "key-1")
        verify = verify_listing(db_path, "test", manifest)
        assert verify["verified"] is False
        assert verify["status"] == "revoked"

    def test_sign_with_nonexistent_key(self, db_path):
        result = sign_listing(db_path, "test", "bad-key", "sig", {})
        assert result["signed"] is False

    def test_sign_with_revoked_key(self, db_path):
        register_key(db_path, "key-1", "Alice", "pubkey")
        revoke_key(db_path, "key-1")
        result = sign_listing(db_path, "test", "key-1", "sig", {})
        assert result["signed"] is False

    def test_get_signature_info(self, db_path):
        register_key(db_path, "key-1", "Alice", "pubkey")
        sign_listing(db_path, "test", "key-1", "sig", {"id": "test"})
        info = get_signature_info(db_path, "test")
        assert info is not None
        assert info["key_id"] == "key-1"
        assert info["author"] == "Alice"

    def test_get_signature_info_none(self, db_path):
        assert get_signature_info(db_path, "nonexistent") is None


class TestSigningAPI:
    def test_register_key_endpoint(self, client):
        resp = client.post("/v1/signing/keys", json={
            "key_id": "test-key-1", "author": "Tester", "public_key": "base64key=="
        })
        assert resp.status_code == 200
        assert resp.json()["registered"] is True

    def test_register_duplicate_key_409(self, client):
        client.post("/v1/signing/keys", json={
            "key_id": "dup-key", "author": "Tester", "public_key": "key"
        })
        resp = client.post("/v1/signing/keys", json={
            "key_id": "dup-key", "author": "Tester", "public_key": "key"
        })
        assert resp.status_code == 409

    def test_get_key_endpoint(self, client):
        client.post("/v1/signing/keys", json={
            "key_id": "get-key", "author": "Tester", "public_key": "pubkey"
        })
        resp = client.get("/v1/signing/keys/get-key")
        assert resp.status_code == 200
        assert resp.json()["author"] == "Tester"

    def test_get_key_not_found(self, client):
        resp = client.get("/v1/signing/keys/nonexistent")
        assert resp.status_code == 404

    def test_revoke_key_endpoint(self, client):
        client.post("/v1/signing/keys", json={
            "key_id": "rev-key", "author": "Tester", "public_key": "key"
        })
        resp = client.delete("/v1/signing/keys/rev-key")
        assert resp.status_code == 200
        assert resp.json()["revoked"] is True

    def test_revoke_nonexistent_key(self, client):
        resp = client.delete("/v1/signing/keys/nope")
        assert resp.status_code == 404

    def test_sign_listing_endpoint(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        client.post("/v1/signing/keys", json={
            "key_id": "sign-key", "author": "Tester", "public_key": "pk"
        })
        resp = client.post(f"/v1/listings/{listing_id}/sign", json={
            "key_id": "sign-key", "signature": "sig==",
            "manifest_data": {"id": listing_id, "title": "Test"}
        })
        assert resp.status_code == 200
        assert resp.json()["signed"] is True

    def test_sign_nonexistent_listing(self, client):
        resp = client.post("/v1/listings/nonexistent-xyz/sign", json={
            "key_id": "k", "signature": "s", "manifest_data": {}
        })
        assert resp.status_code == 404

    def test_verify_listing_endpoint(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        resp = client.get(f"/v1/listings/{listing_id}/verify")
        assert resp.status_code == 200
        data = resp.json()
        assert "verified" in data
        assert "status" in data

    def test_get_signature_endpoint(self, client):
        resp = client.get("/v1/listings?per_page=1")
        listing_id = resp.json()["listings"][0]["id"]
        # No signature yet
        resp = client.get(f"/v1/listings/{listing_id}/signature")
        assert resp.status_code == 404

    def test_author_keys_endpoint(self, client):
        client.post("/v1/signing/keys", json={
            "key_id": "auth-k1", "author": "AuthorX", "public_key": "pk1"
        })
        resp = client.get("/v1/signing/authors/AuthorX/keys")
        assert resp.status_code == 200
        assert len(resp.json()["keys"]) == 1
