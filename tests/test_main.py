"""Offline tests for the SOFFEE MCP server. ESPN is replaced by a fake League; no network calls."""

import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import main  # noqa: E402

SLACK_MAP = {"U111": 1, "U222": 2}


class FakeLeague:
    instances = 0

    def __init__(self, league_id, year, espn_s2, swid):
        FakeLeague.instances += 1
        self.year = year
        self.current_week = 5
        self.settings = SimpleNamespace(name="Test League")
        self.teams = [
            SimpleNamespace(
                team_id=1,
                team_name="Gridiron Gang",
                wins=4,
                losses=0,
                points_for=500.123,
                points_against=400.0,
            ),
            SimpleNamespace(
                team_id=2,
                team_name="Bench Warmers",
                wins=0,
                losses=4,
                points_for=350.0,
                points_against=480.555,
            ),
        ]

    def standings(self):
        return sorted(self.teams, key=lambda t: -t.wins)

    def _pair(self, home, away):
        starter = SimpleNamespace(
            playerId=1,
            name="Starter",
            slot_position="QB",
            points=10.0,
            projected_points=18.0,
        )
        bench = SimpleNamespace(
            playerId=2,
            name="Benchwarmer",
            slot_position="BE",
            points=0.0,
            projected_points=9.0,
        )
        return SimpleNamespace(
            home_team=self.teams[0],
            away_team=self.teams[1],
            home_score=home,
            away_score=away,
            home_projected=110.0,
            away_projected=95.5,
            home_lineup=[starter, bench],
            away_lineup=[],
        )

    def scoreboard(self, week):
        # ESPN's settled totals: still 0 while the week is in progress
        return [
            self._pair(0.0, 0.0)
            if week >= self.current_week
            else self._pair(101.5, 88.25)
        ]

    def box_scores(self, week):
        return [self._pair(23.4, 0.0)]  # live totals


@pytest.fixture(autouse=True)
def fake_espn(monkeypatch):
    for key, value in {
        "ESPN_SWID": "{swid}",
        "ESPN_S2": "s2",
        "ESPN_LEAGUE_ID": "123",
        "ESPN_YEAR": "2026",
        "SOFFEE_SLACK_USER_TO_TEAM_MAP": json.dumps(SLACK_MAP),
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(main, "League", FakeLeague)
    main._league_cache.clear()
    FakeLeague.instances = 0


def test_all_tools_registered():
    names = {t.name for t in asyncio.run(main.mcp.list_tools())}
    assert {
        "get_scoreboard",
        "get_historical_season_summary",
        "get_team_owners",
        "generate_batch_score_summary",
    } <= names


def test_load_env_file_strips_quotes_and_keeps_existing(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nNEW_KEY='{\"a\":1}'\nESPN_YEAR=1999\n")
    monkeypatch.delenv("NEW_KEY", raising=False)
    main.load_env_file(env)
    assert json.loads(main.os.environ["NEW_KEY"]) == {"a": 1}
    assert main.os.environ["ESPN_YEAR"] == "2026"  # already set; not overridden


def test_missing_settings_reported_clearly(monkeypatch):
    monkeypatch.delenv("ESPN_S2")
    result = main.initialize_league()
    assert isinstance(result, main.LeagueInitializationError)
    assert "ESPN_S2" in result.error


def test_league_is_cached_but_fresh_bypasses_cache():
    a, b = main.initialize_league(), main.initialize_league()
    assert a is b and FakeLeague.instances == 1
    assert main.initialize_league(fresh=True) is not a
    assert main.initialize_league() is a  # fresh copies don't replace the shared one


def test_historical_season_summary():
    result = main.get_historical_season_summary(2023)
    assert result["success"], result
    assert result["league_name"] == "Test League"
    assert [t["team_name"] for t in result["standings"]] == [
        "Gridiron Gang",
        "Bench Warmers",
    ]


def test_team_owners_resolve_names():
    result = main.get_team_owners()
    assert result["success"], result
    assert {o["slack_user_id"]: o["team_name"] for o in result["owners"]} == {
        "U111": "Gridiron Gang",
        "U222": "Bench Warmers",
    }


def test_check_reports_ok(capsys):
    assert main.check() == 0
    assert "OK: 'Test League'" in capsys.readouterr().out


def test_scoreboard_uses_live_scores_for_current_week():
    live = main.get_scoreboard()
    assert live["live"] and live["matchups"][0]["home_score"] == 23.4
    past = main.get_scoreboard(week=4)
    assert "live" not in past and past["matchups"][0]["home_score"] == 101.5


def test_batch_summary_reports_live_scores():
    assert "Gridiron Gang: 23.4" in main.generate_batch_score_summary()


def test_live_scoreboard_includes_projections():
    m = main.get_scoreboard()["matchups"][0]
    assert (m["home_projected"], m["away_projected"]) == (110.0, 95.5)


def test_box_scores_hides_bench_and_filters_by_team():
    res = main.get_box_scores()
    assert res["box_scores"][0]["home_lineup"] == [
        "QB Starter — 10.0 pts (proj 18.0) [id 1]"
    ]
    assert (
        len(main.get_box_scores(include_bench=True)["box_scores"][0]["home_lineup"])
        == 2
    )
    home = res["box_scores"][0]["home_team"]
    assert main.get_box_scores(team_name=home[:4].lower())["success"]
    assert not main.get_box_scores(team_name="no such team")["success"]
