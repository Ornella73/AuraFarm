"""Unit tests for Native Speaker Audio Evaluation Studio & Metrics (Step E10)."""
import pytest
from src.core.database import (
    init_db,
    save_audio_evaluation,
    list_audio_evaluations,
    get_audio_evaluations_summary
)
from src.api.main import (
    AudioEvaluationPayload,
    submit_audio_evaluation,
    get_audio_eval_summary,
    list_audio_evals,
    audio_eval_view
)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_save_and_retrieve_audio_evaluations():
    """Test saving individual audio evaluations in SQLite."""
    eval_id_1 = save_audio_evaluation(
        clip_id="status_semer",
        language="ewe",
        clarity_rating=5,
        naturalness_rating=4,
        accent_authenticity_rating=5,
        comprehension_check_passed=True,
        evaluator_name="Akofa Agbodjan",
        evaluator_origin_region="Maritime",
        comments="Accent parfait de la préfecture du Zio."
    )
    assert eval_id_1 > 0

    eval_id_2 = save_audio_evaluation(
        clip_id="status_semer",
        language="kabiye",
        clarity_rating=4,
        naturalness_rating=5,
        accent_authenticity_rating=5,
        comprehension_check_passed=True,
        evaluator_name="Kouma Tchalim",
        evaluator_origin_region="Kara",
        comments="Intonation authentique de Kozah."
    )
    assert eval_id_2 > 0

    # Retrieve by language
    ewe_evals = list_audio_evaluations(language="ewe")
    assert any(e["id"] == eval_id_1 for e in ewe_evals)

    kabiye_evals = list_audio_evaluations(language="kabiye")
    assert any(e["id"] == eval_id_2 for e in kabiye_evals)

def test_audio_evaluations_summary_aggregation():
    """Test aggregation metrics by language and global."""
    save_audio_evaluation(
        clip_id="status_attendre",
        language="mina",
        clarity_rating=4,
        naturalness_rating=4,
        accent_authenticity_rating=4,
        comprehension_check_passed=True,
        evaluator_name="Afi",
        evaluator_origin_region="Maritime"
    )
    save_audio_evaluation(
        clip_id="status_risque",
        language="mina",
        clarity_rating=2,
        naturalness_rating=4,
        accent_authenticity_rating=4,
        comprehension_check_passed=False,
        evaluator_name="Messan",
        evaluator_origin_region="Maritime"
    )

    summary = get_audio_evaluations_summary()
    assert "by_language" in summary
    assert "overall" in summary
    assert "mina" in summary["by_language"]

    mina_stats = summary["by_language"]["mina"]
    assert mina_stats["count"] >= 2
    assert 1.0 <= mina_stats["avg_clarity"] <= 5.0
    assert 0.0 <= mina_stats["comprehension_rate_pct"] <= 100.0

def test_api_audio_eval_endpoints():
    """Test API route functions directly."""
    payload = AudioEvaluationPayload(
        clip_id="variety_recommendation",
        language="francais",
        clarity_rating=5,
        naturalness_rating=5,
        accent_authenticity_rating=4,
        comprehension_check_passed=True,
        evaluator_name="Jury Hackathon",
        evaluator_origin_region="Maritime",
        comments="Message clair, concis et actionnable en moins de 30 secondes."
    )
    res = submit_audio_evaluation(payload)
    assert res["status"] == "SUCCESS"
    assert "evaluation_id" in res

    # Summary endpoint
    sum_res = get_audio_eval_summary()
    assert "by_language" in sum_res
    assert "francais" in sum_res["by_language"]

    # List endpoint
    list_res = list_audio_evals(language="francais")
    assert isinstance(list_res, list)
    assert len(list_res) >= 1

def test_audio_eval_view_html():
    """Test the HTML evaluation studio rendering."""
    resp = audio_eval_view()
    assert resp.status_code == 200
    assert "text/html" in resp.media_type
    content = resp.body.decode("utf-8")
    assert "AuraFarm • Évaluation Vocale Terroir" in content
    assert "Filtre Haut-Parleur Téléphone 2G" in content
    assert "Loi Togolaise N° 2019-014" in content
    assert "summary-cards-container" in content
    assert "recent-reviews-list" in content

