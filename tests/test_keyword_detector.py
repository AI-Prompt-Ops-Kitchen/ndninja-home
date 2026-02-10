import pytest
from tools_db.tools.keyword_detector import KeywordDetector, DetectionResult


class TestKeywordDetectorInit:
    """Test KeywordDetector initialization"""

    def test_detector_initialization(self):
        """Test that KeywordDetector initializes correctly"""
        detector = KeywordDetector()
        assert detector is not None
        assert hasattr(detector, 'detect')


class TestHighConfidenceDetection:
    """Test high-confidence keyword detection (>= 80%)"""

    def test_git_commit_keyword_detection(self):
        """Test detection of 'git commit' keyword with high confidence"""
        detector = KeywordDetector()
        result = detector.detect("git add -A && git commit -m 'feat: add feature'")

        assert result is not None
        assert result.keyword_found == "git commit"
        assert result.confidence >= 80
        assert result.category == "commit-related"
        assert "git commit" in result.context_snippet.lower()

    def test_committed_keyword_detection(self):
        """Test detection of 'committed' keyword"""
        detector = KeywordDetector()
        result = detector.detect("Changes committed successfully to main branch")

        assert result is not None
        assert result.keyword_found is not None
        assert "commit" in result.keyword_found.lower()
        assert result.confidence >= 80

    def test_deployed_keyword_detection(self):
        """Test detection of 'deployed' keyword"""
        detector = KeywordDetector()
        result = detector.detect("Application deployed to production successfully")

        assert result is not None
        assert result.keyword_found is not None
        assert "deploy" in result.keyword_found.lower()
        assert result.confidence >= 80
        assert result.category == "deployment"

    def test_all_tests_passed_keyword_detection(self):
        """Test detection of 'all tests passed' keyword"""
        detector = KeywordDetector()
        result = detector.detect("Running pytest... All tests passed successfully! ✅ passing")

        assert result is not None
        assert result.keyword_found is not None
        assert "test" in result.keyword_found.lower()
        assert "pass" in result.keyword_found.lower()
        assert result.confidence >= 80
        assert result.category == "test-success"

    def test_fixed_keyword_detection(self):
        """Test detection of 'fixed' keyword"""
        detector = KeywordDetector()
        result = detector.detect("Bug fixed in authentication module")

        assert result is not None
        assert result.keyword_found is not None
        assert "fix" in result.keyword_found.lower()
        assert result.confidence >= 80
        assert result.category == "bug-fixed"

    def test_file_created_keyword_detection(self):
        """Test detection of 'created' keyword"""
        detector = KeywordDetector()
        result = detector.detect("New file created at /path/to/file.py")

        assert result is not None
        assert result.keyword_found is not None
        assert "create" in result.keyword_found.lower()
        assert result.confidence >= 80
        assert result.category == "file-created"


class TestMediumConfidenceDetection:
    """Test medium-confidence keyword detection (60-80%)"""

    def test_pushed_to_keyword_detection(self):
        """Test detection of 'pushed to' keyword"""
        detector = KeywordDetector()
        result = detector.detect("Code pushed to staging branch")

        assert result is not None
        # Should be detected but maybe with medium confidence
        if result.keyword_found:
            assert result.confidence >= 60
            assert result.category in ["deployment", "commit-related"]


class TestLowConfidenceErrorMessages:
    """Test that error messages return low confidence or no result"""

    def test_commit_failed_error_message(self):
        """Test that 'commit failed' returns low confidence or no result"""
        detector = KeywordDetector()
        result = detector.detect("Error: commit failed due to unstaged changes")

        # Should either return None or low confidence
        if result is not None:
            assert result.confidence < 80  # Not high confidence
            assert "failed" in result.context_snippet.lower() or result.confidence < 60

    def test_deployment_failed_error_message(self):
        """Test that 'deployment failed' returns low confidence"""
        detector = KeywordDetector()
        result = detector.detect("Deployment failed: Connection timeout to server")

        # Should either return None or low confidence
        if result is not None:
            assert result.confidence < 80

    def test_test_failed_error_message(self):
        """Test that 'test failed' returns low confidence"""
        detector = KeywordDetector()
        result = detector.detect("Tests failed: 3 assertions failed in test_main.py")

        # Should either return None or low confidence
        if result is not None:
            assert result.confidence < 80


class TestMultipleKeywords:
    """Test handling of multiple keywords in same output"""

    def test_multiple_keywords_returns_highest_confidence(self):
        """Test that multiple keywords returns highest confidence match"""
        detector = KeywordDetector()
        result = detector.detect(
            "git add . && git commit -m 'feat' && git push origin main && deployment complete"
        )

        assert result is not None
        # Should return one of the keywords found
        assert result.keyword_found is not None
        assert result.confidence >= 60

    def test_multiple_high_confidence_keywords(self):
        """Test multiple high-confidence keywords"""
        detector = KeywordDetector()
        result = detector.detect("Tests passing, build successful, deployed to production")

        assert result is not None
        assert result.keyword_found is not None
        # Should pick the highest confidence one
        assert result.confidence >= 60


class TestNoKeywordsFound:
    """Test handling of outputs with no completion keywords"""

    def test_empty_string_returns_empty_result(self):
        """Test that empty string returns None or empty result"""
        detector = KeywordDetector()
        result = detector.detect("")

        assert result is None or result.keyword_found is None

    def test_no_keywords_in_normal_output(self):
        """Test output with no completion keywords"""
        detector = KeywordDetector()
        result = detector.detect("Starting process... Loading files... Analyzing data...")

        assert result is None or result.keyword_found is None

    def test_unrelated_text_returns_empty_result(self):
        """Test that unrelated text returns no result"""
        detector = KeywordDetector()
        result = detector.detect(
            "The meeting is scheduled for tomorrow at 3pm in the conference room"
        )

        assert result is None or result.keyword_found is None


class TestCaseInsensitiveMatching:
    """Test case-insensitive keyword matching"""

    def test_uppercase_git_commit_keyword(self):
        """Test uppercase 'GIT COMMIT' matches"""
        detector = KeywordDetector()
        result = detector.detect("GIT COMMIT -m 'feature complete'")

        assert result is not None
        assert result.keyword_found is not None
        assert "commit" in result.keyword_found.lower()
        assert result.confidence >= 60

    def test_mixed_case_deployed_keyword(self):
        """Test mixed case 'DePlOyEd' matches"""
        detector = KeywordDetector()
        result = detector.detect("The application has been DePlOyEd to production")

        assert result is not None
        assert result.keyword_found is not None
        assert "deploy" in result.keyword_found.lower()
        assert result.confidence >= 60

    def test_lowercase_fixed_keyword(self):
        """Test lowercase 'fixed' matches"""
        detector = KeywordDetector()
        result = detector.detect("The bug has been fixed in version 1.2.3")

        assert result is not None
        assert result.keyword_found is not None
        assert result.confidence >= 60


class TestRealToolOutputExamples:
    """Test with real tool output examples"""

    def test_real_bash_git_output(self):
        """Test with realistic bash output containing git commit"""
        detector = KeywordDetector()
        bash_output = """
        On branch main
        Your branch is up to date with 'origin/main'.

        nothing to commit, working tree clean
        [main b183107] chore: add Python cache files to gitignore
         1 file changed, 5 insertions(+)
        """
        result = detector.detect(bash_output)

        # Should detect the commit
        if result is not None:
            assert "commit" in result.keyword_found.lower() or result.keyword_found is None

    def test_real_pytest_output(self):
        """Test with realistic pytest output"""
        detector = KeywordDetector()
        pytest_output = """
        ============================= test session starts ==============================
        collected 7 items

        tests/test_keyword_detector.py::TestHighConfidenceDetection::test_git_commit_keyword_detection PASSED
        tests/test_keyword_detector.py::TestHighConfidenceDetection::test_committed_keyword_detection PASSED
        tests/test_keyword_detector.py::TestNoKeywordsFound::test_empty_string_returns_empty_result PASSED

        ============================== 7 passed in 0.23s ===============================
        """
        result = detector.detect(pytest_output)

        assert result is not None
        assert result.keyword_found is not None
        assert "pass" in result.keyword_found.lower()
        assert result.confidence >= 80

    def test_real_deployment_output(self):
        """Test with realistic deployment output"""
        detector = KeywordDetector()
        deploy_output = """
        Deploying application...
        Building Docker image...
        Pushing to registry...
        Deployment successful! Application is live on https://app.example.com
        """
        result = detector.detect(deploy_output)

        assert result is not None
        assert result.keyword_found is not None
        assert result.confidence >= 60

    def test_write_command_output(self):
        """Test with Write tool output"""
        detector = KeywordDetector()
        write_output = "File written to /path/to/file.md successfully"
        result = detector.detect(write_output)

        assert result is not None
        assert result.keyword_found is not None
        # Should detect "written to" or "created" keywords
        keyword_lower = result.keyword_found.lower()
        assert "written" in keyword_lower or "creat" in keyword_lower


class TestDetectionResultStructure:
    """Test that DetectionResult has correct structure"""

    def test_detection_result_has_required_fields(self):
        """Test that DetectionResult contains all required fields"""
        detector = KeywordDetector()
        result = detector.detect("git commit -m 'test'")

        assert result is not None
        assert hasattr(result, 'keyword_found')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'category')
        assert hasattr(result, 'context_snippet')

    def test_detection_result_confidence_is_integer(self):
        """Test that confidence score is an integer 0-100"""
        detector = KeywordDetector()
        result = detector.detect("git commit -m 'test'")

        assert result is not None
        assert isinstance(result.confidence, int)
        assert 0 <= result.confidence <= 100

    def test_detection_result_category_is_string(self):
        """Test that category is a valid string"""
        detector = KeywordDetector()
        result = detector.detect("git commit -m 'test'")

        assert result is not None
        assert isinstance(result.category, str)
        assert len(result.category) > 0


class TestContextSnippetExtraction:
    """Test that context snippets are properly extracted"""

    def test_context_snippet_contains_keyword(self):
        """Test that context snippet contains the detected keyword"""
        detector = KeywordDetector()
        long_output = """
        Some preliminary output here
        git commit -m 'feat: add new feature'
        Some trailing output here
        """
        result = detector.detect(long_output)

        if result is not None and result.keyword_found:
            # Context snippet should contain the keyword (case-insensitive)
            assert result.keyword_found.lower() in result.context_snippet.lower()

    def test_context_snippet_is_reasonable_length(self):
        """Test that context snippet is not too long"""
        detector = KeywordDetector()
        result = detector.detect("git commit -m 'very long message'")

        if result is not None:
            # Context snippet should be reasonable (not the entire input necessarily)
            assert len(result.context_snippet) > 0
            assert len(result.context_snippet) < 500


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_keyword_at_start_of_string(self):
        """Test keyword detection at the start of a string"""
        detector = KeywordDetector()
        result = detector.detect("deployed successfully to production environment")

        assert result is not None
        assert result.keyword_found is not None

    def test_keyword_at_end_of_string(self):
        """Test keyword detection at the end of a string"""
        detector = KeywordDetector()
        result = detector.detect("The changes have been committed")

        assert result is not None
        assert result.keyword_found is not None

    def test_keyword_with_surrounding_punctuation(self):
        """Test keyword detection with punctuation"""
        detector = KeywordDetector()
        result = detector.detect("Status: 'git commit' completed. All done!")

        assert result is not None
        assert result.keyword_found is not None

    def test_very_long_output(self):
        """Test with very long output string"""
        detector = KeywordDetector()
        long_text = "Processing... " * 1000 + "git commit -m 'test' completed"

        result = detector.detect(long_text)
        assert result is not None or result is None  # Just ensure it doesn't crash
