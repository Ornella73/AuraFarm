"""Playwright E2E test for the Audio Recorder Studio (/audio-recorder)."""
import re
from playwright.sync_api import Page, expect

def test_audio_recorder_page_elements(page: Page):
    # Navigate to audio recorder page (assuming test server or file)
    page.goto("http://localhost:8000/audio-recorder")

    # 1. Header and branding
    expect(page.locator("h1")).to_contain_text("AuraFarm • Studio Vocale Terroir")

    # 2. Speaker input and consent checkbox
    speaker_input = page.locator("#speaker-id")
    expect(speaker_input).to_be_visible()

    consent_check = page.locator("#consent-check")
    expect(consent_check).to_be_checked()

    # 3. Language selector
    lang_select = page.locator("#select-language")
    expect(lang_select).to_be_visible()
    expect(lang_select).to_have_value("ewe")

    # 4. Table containing phrases
    phrases_rows = page.locator("#phrases-tbody tr")
    expect(phrases_rows.first).to_be_visible()

    # 5. Filter category buttons
    cat_buttons = page.locator("#filter-buttons button")
    expect(cat_buttons).to_have_count(6)

