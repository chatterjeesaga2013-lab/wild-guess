"""Small tests that do not need network access or Streamlit to run."""

import sys
import types
import unittest
from unittest.mock import MagicMock, patch

from game import ANIMALS, FEATURES, MAX_TURNS, finish_game, game_summary, new_game, play_turn
from llm import local_intent, parse_json, interpret


class GameTests(unittest.TestCase):
    def test_feature_eliminates_and_keeps_answer(self):
        game = new_game("tiger")
        ok, reply, record = play_turn(game, "Does it have stripes?", {"kind": "feature", "value": "stripes"})
        self.assertTrue(ok)
        self.assertIsNone(record)
        self.assertIn("Yes", reply)
        self.assertIn("tiger", game["candidates"])
        self.assertLess(len(game["candidates"]), len(ANIMALS))
        t = game["turns"][0]
        self.assertAlmostEqual(t["quality"], round(100 * t["removed"] / t["before"], 1))

    def test_wrong_guess_cannot_remove_target(self):
        game = new_game("tiger")
        ok, _, record = play_turn(game, "lion", {"kind": "guess", "value": "lion"})
        self.assertTrue(ok)
        self.assertIsNone(record)
        self.assertNotIn("lion", game["candidates"])
        self.assertIn("tiger", game["candidates"])

    def test_win_is_recorded_once(self):
        game = new_game("polar bear")
        ok, _, record = play_turn(game, "polar bear", {"kind": "guess", "value": "polar bear"})
        self.assertTrue(ok)
        self.assertEqual(record["outcome"], "Won")
        self.assertEqual(record["guesses"], 1)
        self.assertIsNone(finish_game(game, "Won"))
        self.assertEqual(game_summary([record])["games"], 1)

    def test_invalid_intent_does_not_consume_turn(self):
        game = new_game("owl")
        for inp, action in [("", {"kind": "guess", "value": "owl"}),
                            ("?" * 241, {"kind": "feature", "value": "bird"}),
                            ("please dance", {"kind": "unknown", "value": ""}),
                            ("is it a unicorn?", {"kind": "guess", "value": "unicorn"})]:
            ok, _, _ = play_turn(game, inp, action)
            self.assertFalse(ok)
        self.assertEqual(len(game["turns"]), 0)

    def test_repeated_question_scores_zero(self):
        game = new_game("bat")
        for _ in range(2):
            play_turn(game, "Does it fly?", {"kind": "feature", "value": "flies"})
        self.assertEqual(game["turns"][1]["quality"], 0)

    def test_timeout_and_loss(self):
        game = new_game("zebra")
        result = None
        for _ in range(MAX_TURNS):
            _, _, result = play_turn(game, "Is it a bird?", {"kind": "feature", "value": "bird"})
        self.assertEqual(result["outcome"], "Lost")
        self.assertEqual(result["guesses"], MAX_TURNS)

    def test_all_facts_defined(self):
        for animal, facts in ANIMALS.items():
            self.assertTrue(facts.issubset(FEATURES), animal)
        self.assertEqual(len(ANIMALS), 30)

    def test_offline_parser(self):
        examples = {
            "is it a tiger?": ("guess", "tiger"),
            "shark": ("guess", "great white shark"),
            "does it have stripes?": ("feature", "stripes"),
            "is it a mammal?": ("feature", "mammal"),
            "can it fly?": ("feature", "flies"),
            "does it lay eggs?": ("feature", "eggs"),
        }
        for phrase, (kind, value) in examples.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(local_intent(phrase), {"kind": kind, "value": value})

    def test_offline_mode_works_without_secrets(self):
        intent, source = interpret("Can it fly?", {})
        self.assertEqual(source, "offline")
        self.assertEqual(intent, {"kind": "feature", "value": "flies"})

    def test_ai_interpreter_uses_validated_json(self):
        client = MagicMock()
        client.chat.completions.create.return_value.choices[0].message.content = (
            '{"kind":"feature","value":"nocturnal"}'
        )
        fake_openai = types.ModuleType("openai")
        fake_openai.OpenAI = lambda **kwargs: client
        with patch.dict(sys.modules, {"openai": fake_openai}):
            intent, source = interpret("Is it mostly awake at night?", {
                "key": "mock-key", "url": "https://example.org/v1", "model": "test-model"
            })
        self.assertEqual((intent, source), ({"kind": "feature", "value": "nocturnal"}, "AI"))

    def test_api_error_gracefully_falls_back(self):
        fake_openai = types.ModuleType("openai")
        fake_openai.OpenAI = MagicMock(side_effect=RuntimeError("offline"))
        with patch.dict(sys.modules, {"openai": fake_openai}):
            intent, source = interpret("Does it have stripes?", {
                "key": "mock-key", "url": "https://example.org/v1", "model": "test-model"
            })
        self.assertEqual((intent, source), ({"kind": "feature", "value": "stripes"}, "offline"))

    def test_llm_response_validation(self):
        self.assertEqual(parse_json('```json\n{"kind":"guess","value":"rhino"}\n```'),
                         {"kind": "guess", "value": "rhinoceros"})
        self.assertIsNone(parse_json('{"kind":"feature","value":"mind_reading"}'))
        self.assertIsNone(parse_json('not json'))


if __name__ == "__main__":
    unittest.main()
