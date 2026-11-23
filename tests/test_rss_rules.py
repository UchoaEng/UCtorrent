from uctorrent.app.services.rss_rules_service import RssRulesService


def test_rss_rule_matching():
    service = RssRulesService()
    rule = {"must_contain": "ubuntu", "must_not_contain": "beta", "regex": r"22\.04"}
    assert service.matches("Ubuntu 22.04 ISO", rule)
    assert not service.matches("Ubuntu beta 22.04 ISO", rule)
    assert not service.matches("Debian 12 ISO", rule)

