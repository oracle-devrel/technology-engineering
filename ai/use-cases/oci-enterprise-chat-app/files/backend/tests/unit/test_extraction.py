"""Unit tests for the extraction service."""

import pytest

from services.extraction import ExtractionService
from models.document import ExtractedParameter


class TestExtractionService:
    """Tests for ExtractionService class."""

    def test_init(self) -> None:
        """Test service initialization."""
        service = ExtractionService()
        assert service is not None

    def test_extract_dates(
        self,
        extraction_service: ExtractionService,
        sample_document_text: str,
    ) -> None:
        """Test extraction identifies dates."""
        parameters = extraction_service._extract(sample_document_text)

        date_params = [p for p in parameters if p.name == "Date"]
        assert len(date_params) > 0
        assert any("January 15, 2024" in str(p.value) for p in date_params)

    def test_extract_amounts(
        self,
        extraction_service: ExtractionService,
        sample_document_text: str,
    ) -> None:
        """Test extraction identifies monetary amounts."""
        parameters = extraction_service._extract(sample_document_text)

        amount_params = [p for p in parameters if p.name == "Amount"]
        assert len(amount_params) > 0
        assert any("150,000" in str(p.value) for p in amount_params)

    def test_extract_emails(
        self,
        extraction_service: ExtractionService,
        sample_document_text: str,
    ) -> None:
        """Test extraction identifies email addresses."""
        parameters = extraction_service._extract(sample_document_text)

        email_params = [p for p in parameters if p.name == "Email"]
        assert len(email_params) > 0
        assert any("sales@abc-corp.com" in str(p.value) for p in email_params)

    def test_extract_phones(
        self,
        extraction_service: ExtractionService,
        sample_document_text: str,
    ) -> None:
        """Test extraction identifies phone numbers."""
        parameters = extraction_service._extract(sample_document_text)

        phone_params = [p for p in parameters if p.name == "Phone Number"]
        assert len(phone_params) > 0

    def test_extract_percentages(
        self,
        extraction_service: ExtractionService,
        sample_document_text: str,
    ) -> None:
        """Test extraction identifies percentages."""
        parameters = extraction_service._extract(sample_document_text)

        pct_params = [p for p in parameters if p.name == "Percentage"]
        assert len(pct_params) > 0
        assert any("20%" in str(p.value) or "5.5%" in str(p.value) for p in pct_params)

    def test_extract_removes_duplicates(
        self,
        extraction_service: ExtractionService,
    ) -> None:
        """Test that extraction removes duplicate values."""
        text = """
        Date: 01/15/2024
        Another date: 01/15/2024
        Amount: $100.00
        Total: $100.00
        """

        parameters = extraction_service._extract(text)

        # Each unique value should appear only once
        values = [p.value for p in parameters]
        assert len(values) == len(set(values))

    def test_extract_limits_results(
        self,
        extraction_service: ExtractionService,
    ) -> None:
        """Test that extraction limits results to 50."""
        # Generate text with many extractable values
        dates = " ".join([f"01/{i:02d}/2024" for i in range(1, 32)])
        amounts = " ".join([f"${i * 100}.00" for i in range(1, 50)])
        text = f"Dates: {dates}\nAmounts: {amounts}"

        parameters = extraction_service._extract(text)

        assert len(parameters) <= 50

    @pytest.mark.asyncio
    async def test_extract_parameters_empty_text(
        self,
        extraction_service: ExtractionService,
    ) -> None:
        """Test extraction with empty document text."""
        result = await extraction_service.extract_parameters("   ")

        assert len(result.parameters) == 0
        assert result.error_message == "Document text is empty"
