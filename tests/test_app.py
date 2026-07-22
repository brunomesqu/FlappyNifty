import unittest
from pathlib import Path

from app import Score, app, db, normalize_skin_key


class FlappyNiftyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        )

    def setUp(self):
        with app.app_context():
            db.drop_all()
            db.create_all()
        self.client = app.test_client()

    def test_legacy_skin_keys_normalize(self):
        expected = {
            "Sniffyffy": "Lafyfty",
            "Swiffy": "Swifty",
            "Taylor Sniffy": "Swifty",
            "Sniffychu": "Niftychu",
            "Swiffychu": "Niftychu",
            "Sniffy the Hedgehog": "Hedgehog",
            "Nifty the Hedgehog": "Hedgehog",
        }
        for old_key, new_key in expected.items():
            self.assertEqual(normalize_skin_key(old_key), new_key)
        self.assertEqual(normalize_skin_key("Classic"), "Classic")

    def test_cached_client_submission_uses_canonical_skin(self):
        run_response = self.client.post("/start_run", json={"meta": "test"})
        run_id = run_response.get_json()["runId"]
        response = self.client.post(
            "/submit_score",
            json={
                "name": "Tester",
                "section": "General",
                "score": 1,
                "skin": "Swiffy",
                "runId": run_id,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["skin"], "Swifty")

    def test_existing_legacy_scores_are_migrated(self):
        with app.app_context():
            db.session.add(Score(name="Legacy", section="A", score=4, skin="Sniffychu"))
            db.session.commit()
        self.client.get("/")
        with app.app_context():
            self.assertEqual(Score.query.one().skin, "Niftychu")

    def test_brand_and_assets_are_current(self):
        response = self.client.get("/")
        self.assertIn(b"Flappy Nifty", response.data)
        root = Path(__file__).resolve().parents[1]
        script = (root / "static" / "main.js").read_text(encoding="utf-8")
        for label in ("Flappy Nifty", "Lafyfty", "Swifty", "Niftychu"):
            self.assertIn(label, script)
        for asset in (
            "static/assets/nifty.webm",
            "static/assets/flappy-nifty-cover.png",
            "static/assets/icons/Lafyfty.webp",
            "static/assets/icons/Swifty.webp",
            "static/assets/icons/Niftychu.webp",
        ):
            self.assertTrue((root / asset).is_file(), asset)


if __name__ == "__main__":
    unittest.main()
