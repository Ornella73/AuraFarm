"""Playwright E2E test for the 4-block traceable dashboard fiches (Step E4)."""
from playwright.sync_api import Page, expect

def test_dashboard_fiches_4_blocks_and_error_case(page: Page):
    # 1. Navigate to dashboard
    page.goto("http://localhost:8000/dashboard")

    # Wait for cards container to load fiches
    page.wait_for_selector(".fiche-card")
    cards = page.locator(".fiche-card")
    expect(cards.first).to_be_visible()

    count = cards.count()
    assert count >= 3, f"Expected at least 3 cards on dashboard, got {count}"

    # 2. Check 4 blocks on the first 3 fiches
    for i in range(min(3, count)):
        card = cards.nth(i)

        # Bloc D : Bandeau de contrôle
        banner = card.locator(".bloc-d-banner")
        expect(banner).to_be_visible()

        # Bloc A : Entrées
        bloc_a = card.locator(".bloc-a-entries")
        expect(bloc_a).to_be_visible()
        expect(bloc_a).to_contain_text("Calcul :")
        expect(bloc_a).to_contain_text("Source Pluie :")

        # Bloc B : Calcul
        bloc_b = card.locator(".bloc-b-calc")
        expect(bloc_b).to_be_visible()
        expect(bloc_b).to_contain_text("Pluie 3j / Seuil")
        expect(bloc_b).to_contain_text("Règle agro-climatique déclenchée :")

        # Bloc C : Sortie
        bloc_c = card.locator(".bloc-c-output")
        expect(bloc_c).to_be_visible()
        expect(bloc_c.locator(".status-badge")).to_be_visible()
        expect(bloc_c).to_contain_text("Variété homologuée ITRA :")

    # 3. Test Error Case: Click "⛔ Périmée J-10 (Sécurité)"
    stale_btn = page.locator("button:has-text('Périmée J-10')")
    expect(stale_btn).to_be_visible()
    stale_btn.click()

    # Cards must update to show RED banner with DONNÉE PÉRIMÉE and forced ATTENDRE
    page.wait_for_selector(".banner-stale")
    stale_banner = page.locator(".banner-stale").first
    expect(stale_banner).to_be_visible()
    expect(stale_banner).to_contain_text("DONNÉE PÉRIMÉE")

    # Status must be forced to ATTENDRE (CONSULTER AGENT)
    forced_status = page.locator(".status-consulter").first
    expect(forced_status).to_be_visible()
    expect(forced_status).to_contain_text("CONSULTER AGENT")

