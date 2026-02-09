import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from unittest.mock import AsyncMock, patch


async def test_evaluation_job_calls_service(session):
    with patch(
        "app.services.evaluation_service.EvaluationService.evaluate_all",
        new_callable=AsyncMock
    ) as mock_eval:
        from app.services.evaluation_service import EvaluationService

        service = EvaluationService(session)
        await service.evaluate_all()

        mock_eval.assert_called_once()