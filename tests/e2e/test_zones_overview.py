"""Playwright E2E test for the Agro-Climatic Zones Overview page (/zones-overview)."""
from playwright.sync_api import Page, expect

def test_zones_overview_page_elements(page: Page):
    # Navigate to zones overview page
    page.goto("http://localhost:8000/zones-overview")

    # 1. Header and branding
    expect(page.locator("h1")).to_contain_text("AuraFarm • Profils Agro-Climatiques Régionaux")

    # 2. Zone cards container
    zones_container = page.locator("#zones-container")
    expect(zones_container).to_be_visible()

    # 3. Simulation button
    sim_button = page.locator("button:has-text('Simuler 30 saisons')")
    expect(sim_button).to_be_visible()

    # 4. Results table structure
    results_table = page.locator("#sim-tbody")
    expect(results_table).to_be_visible()

