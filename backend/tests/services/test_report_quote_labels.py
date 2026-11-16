import pytest

from app.config import Config
from app.services.report_agent.manager_markdown import _render_simulated_quote_blocks


@pytest.mark.parametrize('language,title,detail', [
    ('Simplified Chinese', '模拟人物发言', '引用详情'),
    ('English', 'Simulated persona statement', 'Citation details'),
    ('German', 'Simulierter Persona-O-Ton', 'Zitatdetails'),
])
def test_quote_labels_follow_report_language_with_traceable_collapsed_details(language, title, detail):
    text = '<simulated_quote persona_id="外媒_898" seed_anchor="ev_98953b7586d524195bdfef23d3b4aea9">这是模拟发言。\n第二行。</simulated_quote>'
    result = _render_simulated_quote_blocks(text, language)
    assert f'**{title}** | 外媒_898' in result
    assert f'<summary>{detail}</summary>' in result
    assert '> 这是模拟发言。\n> 第二行。' in result
    assert 'ev_98953b7586d524195bdfef23d3b4aea9' in result
    assert '<details open' not in result
    assert '<simulated_quote' not in result
    assert _render_simulated_quote_blocks(result, language) == result


def test_default_uses_configured_report_language(monkeypatch):
    monkeypatch.setattr(Config, 'REPORT_LANGUAGE', 'zh-CN')
    result = _render_simulated_quote_blocks('<simulated_quote>发言</simulated_quote>')
    assert '**模拟人物发言**' in result
    assert '未知' in result
    assert 'Simulierter' not in result


def test_quote_identifiers_are_escaped_as_text():
    result = _render_simulated_quote_blocks('<simulated_quote persona_id="<img" seed_anchor="ev_123&456">发言</simulated_quote>', 'zh')
    assert '<img' not in result
    assert '&lt;img' in result
    assert 'ev_123&amp;456' in result
