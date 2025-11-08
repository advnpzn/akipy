"""Tests for constants and dictionaries"""

from akipy.dicts import HEADERS, LANG_MAP, THEME_ID, THEMES, ANSWERS, ANSWER_MAP


class TestHeaders:
    """Tests for HEADERS constant"""

    def test_headers_contains_required_fields(self):
        """Test that HEADERS contains all required fields"""
        assert "Accept" in HEADERS
        assert "Accept-Encoding" in HEADERS
        assert "Accept-Language" in HEADERS
        assert "User-Agent" in HEADERS
        assert "x-requested-with" in HEADERS

    def test_headers_user_agent_is_set(self):
        """Test that User-Agent is properly set"""
        assert "Mozilla" in HEADERS["User-Agent"]

    def test_headers_x_requested_with(self):
        """Test that x-requested-with is XMLHttpRequest"""
        assert HEADERS["x-requested-with"] == "XMLHttpRequest"


class TestLangMap:
    """Tests for LANG_MAP constant"""

    def test_lang_map_contains_english(self):
        """Test that LANG_MAP contains English"""
        assert "english" in LANG_MAP
        assert LANG_MAP["english"] == "en"

    def test_lang_map_contains_common_languages(self):
        """Test that LANG_MAP contains common languages"""
        common_langs = ["english", "spanish", "french", "german", "italian"]
        for lang in common_langs:
            assert lang in LANG_MAP

    def test_lang_map_values_are_two_letter_codes(self):
        """Test that all language codes are 2 characters"""
        for code in LANG_MAP.values():
            assert len(code) == 2

    def test_lang_map_has_arabic(self):
        """Test that LANG_MAP includes Arabic"""
        assert "arabic" in LANG_MAP
        assert LANG_MAP["arabic"] == "ar"

    def test_lang_map_has_asian_languages(self):
        """Test that LANG_MAP includes Asian languages"""
        assert "chinese" in LANG_MAP
        assert "japanese" in LANG_MAP
        assert "korean" in LANG_MAP


class TestThemeId:
    """Tests for THEME_ID constant"""

    def test_theme_id_contains_characters(self):
        """Test that THEME_ID contains characters theme"""
        assert "c" in THEME_ID
        assert THEME_ID["c"] == 1

    def test_theme_id_contains_animals(self):
        """Test that THEME_ID contains animals theme"""
        assert "a" in THEME_ID
        assert THEME_ID["a"] == 14

    def test_theme_id_contains_objects(self):
        """Test that THEME_ID contains objects theme"""
        assert "o" in THEME_ID
        assert THEME_ID["o"] == 2

    def test_theme_id_has_three_themes(self):
        """Test that there are exactly 3 themes"""
        assert len(THEME_ID) == 3


class TestThemes:
    """Tests for THEMES constant"""

    def test_themes_english_has_all_themes(self):
        """Test that English has all three themes"""
        assert "en" in THEMES
        assert "c" in THEMES["en"]
        assert "a" in THEMES["en"]
        assert "o" in THEMES["en"]

    def test_themes_french_has_all_themes(self):
        """Test that French has all three themes"""
        assert "fr" in THEMES
        assert len(THEMES["fr"]) == 3

    def test_themes_all_languages_have_characters(self):
        """Test that all languages support characters theme"""
        for lang, themes in THEMES.items():
            assert "c" in themes, f"Language {lang} should have characters theme"

    def test_themes_contains_all_lang_codes(self):
        """Test that THEMES contains entries for supported languages"""
        for lang_code in LANG_MAP.values():
            assert lang_code in THEMES, f"Language code {lang_code} should be in THEMES"


class TestAnswers:
    """Tests for ANSWERS constant"""

    def test_answers_yes_is_zero(self):
        """Test that 'yes' answers map to 0"""
        assert 0 in ANSWERS
        assert "yes" in ANSWERS[0]
        assert "y" in ANSWERS[0]
        assert "0" in ANSWERS[0]

    def test_answers_no_is_one(self):
        """Test that 'no' answers map to 1"""
        assert 1 in ANSWERS
        assert "no" in ANSWERS[1]
        assert "n" in ANSWERS[1]
        assert "1" in ANSWERS[1]

    def test_answers_idk_is_two(self):
        """Test that 'I don't know' answers map to 2"""
        assert 2 in ANSWERS
        assert "i" in ANSWERS[2]
        assert "idk" in ANSWERS[2]
        assert "i dont know" in ANSWERS[2]
        assert "i don't know" in ANSWERS[2]

    def test_answers_probably_is_three(self):
        """Test that 'probably' answers map to 3"""
        assert 3 in ANSWERS
        assert "p" in ANSWERS[3]
        assert "probably" in ANSWERS[3]

    def test_answers_probably_not_is_four(self):
        """Test that 'probably not' answers map to 4"""
        assert 4 in ANSWERS
        assert "pn" in ANSWERS[4]
        assert "probably not" in ANSWERS[4]

    def test_answers_has_five_options(self):
        """Test that there are exactly 5 answer options"""
        assert len(ANSWERS) == 5


class TestAnswerMap:
    """Tests for ANSWER_MAP constant"""

    def test_answer_map_yes_variations(self):
        """Test that all 'yes' variations are in ANSWER_MAP"""
        assert ANSWER_MAP["yes"] == 0
        assert ANSWER_MAP["y"] == 0
        assert ANSWER_MAP["0"] == 0

    def test_answer_map_no_variations(self):
        """Test that all 'no' variations are in ANSWER_MAP"""
        assert ANSWER_MAP["no"] == 1
        assert ANSWER_MAP["n"] == 1
        assert ANSWER_MAP["1"] == 1

    def test_answer_map_is_reverse_of_answers(self):
        """Test that ANSWER_MAP is the reverse mapping of ANSWERS"""
        for answer_id, variations in ANSWERS.items():
            for variation in variations:
                assert ANSWER_MAP[variation] == answer_id

    def test_answer_map_contains_all_variations(self):
        """Test that ANSWER_MAP contains all answer variations"""
        total_variations = sum(len(variations) for variations in ANSWERS.values())
        assert len(ANSWER_MAP) == total_variations
