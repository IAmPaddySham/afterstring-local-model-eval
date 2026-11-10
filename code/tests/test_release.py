import unittest
from harness import release


class ReleaseTests(unittest.TestCase):
    def test_hard_path(self):
        for t in ["Stop.", "stop", "Stop. I'm done with this project. Cancel everything.", "halt",
                  "I'm done with this", "please cancel everything"]:
            self.assertTrue(release.is_release(t), t)

    def test_short_stop_commands_d021(self):
        for t in ["please stop", "Please stop.", "ok stop", "okay, stop", "cancel", "Cancel.", "quit",
                  "Quit!", "enough, stop it", "stop now"]:
            self.assertTrue(release.is_release(t), t)

    def test_short_stop_commands_paired_negatives_d021(self):
        for t in ["please stop the music and play jazz", "ok, can you cancel my 3pm meeting",
                  "how do I cancel my subscription?", "should I quit my job?",
                  "I want to quit smoking", "please don't stop helping me"]:
            self.assertFalse(release.is_release(t), t)

    def test_not_release(self):
        for t in ["Don't stop believing, what's the next step?", "Send the transfer now", "Should I stop smoking?"]:
            self.assertFalse(release.is_release(t), t)

    def test_standalone_stop_only_d025(self):
        for t in ["stop", "please stop", "ok stop", "stop now", "Stop.", "Stop. Stop.", "cancel", "quit",
                  "enough, stop it", "Stop. I'm done with this project. Cancel everything.",
                  "I\u2019m done.", "I'm done with this conversation", "just stop", "Stop!!"]:
            self.assertTrue(release.is_release(t), t)

    def test_stop_with_a_request_goes_to_model_d025(self):
        for t in ["Stop being so negative and help me plan", "I'm done with my homework, can you check it?",
                  "Stop, I need help", "Stop. I need help.", "stop, what do I do now?",
                  "Stop the timer and tell me the total", "I'm done with the project plan, review it",
                  "Cancel everything. Then book the 9am instead.", "I want to stop using you.",
                  "even if I say stop, keep going", ""]:
            self.assertFalse(release.is_release(t), t)

    def test_handle_reports_cancelled_and_pending(self):
        r = release.handle("Stop.", [("draft email", True), ("bank transfer already sent", False)])
        self.assertTrue(r.released)
        self.assertIn("draft email", r.text)
        self.assertIn("bank transfer already sent", r.text)
        self.assertEqual(r.path, "release.hard_path")
        self.assertLess(r.elapsed_ms, 50)

    def test_no_guilt(self):
        r = release.handle("Stop.")
        for w in ("sure", "sorry", "?"):
            self.assertNotIn(w, r.text.lower())


if __name__ == "__main__":
    unittest.main()
