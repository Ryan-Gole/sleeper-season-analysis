class TableConfig:
    title = ""
    summary_header = ""
    context = []

    def cell(self, team, week_idx, matchup):
        raise NotImplementedError

    def summary(self, matchups):
        raise NotImplementedError


class WLTable(TableConfig):
    title = "📊 Weekly Win/Loss Results"
    summary_header = "Record"

    def cell(self, team, week_idx, matchup, bg=""):
        result = matchup.get("result", "-")
        color = {'W': 'text-green-400', 'L': 'text-red-400', 'D': 'text-yellow-400'}.get(result, 'text-gray-400')
        return f'<td class="border px-2 py-1 text-center {color} {bg}">{result}</td>'

    def summary(self, matchups):
        wins = sum(1 for m in matchups if m.get("result") == 'W')
        losses = sum(1 for m in matchups if m.get("result") == 'L')
        draws = sum(1 for m in matchups if m.get("result") == 'D')
        parts = [f'<span class="text-green-400">{wins}</span>',
                 f'<span class="text-red-400">{losses}</span>']
        if draws:
            parts.append(f'<span class="text-yellow-400">{draws}</span>')
        return '-'.join(parts)


class PointsTable(TableConfig):
    title = "📈 Weekly Points Scored"
    summary_header = "Total"

    def cell(self, team, week_idx, matchup, bg=""):
        points = matchup.get("points_for", 0)
        opp_points = matchup.get("points_against", 0)
        if isinstance(points, (int, float)) and isinstance(opp_points, (int, float)):
            color = 'text-green-400' if points > opp_points else 'text-red-400' if points < opp_points else 'text-yellow-400'
        else:
            color = ''
        return f'<td class="border px-2 py-1 text-center {color} {bg}">{points}</td>'

    def summary(self, matchups):
        total = sum(m.get("points_for", 0) for m in matchups)
        return f"{total:.2f}"


class MarginTable(TableConfig):
    title = "📉 Weekly Point Differentials"
    summary_header = "Total"

    def cell(self, team, week_idx, matchup, bg=""):
        margin = matchup.get("margin", 0)
        if isinstance(margin, (int, float)):
            color = 'text-green-400' if margin > 0 else 'text-red-400' if margin < 0 else 'text-yellow-400'
            display = f"+{margin:.2f}" if margin > 0 else f"{margin:.2f}"
        else:
            color = 'text-gray-400'
            display = "-"
        return f'<td class="border px-2 py-1 text-center {color} {bg}">{display}</td>'

    def summary(self, matchups):
        net = sum(m.get("margin", 0) for m in matchups)
        color = 'text-green-400' if net > 0 else 'text-red-400' if net < 0 else 'text-yellow-400'
        display = f"+{net:.2f}" if net > 0 else f"{net:.2f}"
        return f'<span class="{color}">{display}</span>'


class MaxPointsTable(TableConfig):
    title = "📊 Weekly Max Points"
    summary_header = "Total"
    context = [
        "A green number indicates your Max Points was greater than your opponent's Max Points."
    ]

    def cell(self, team, week_idx, matchup, bg=""):
        max_pts = matchup.get("max_points", 0)
        opp_max_pts = matchup.get("opp_max_points", 0)
        color = ''
        if isinstance(max_pts, (int, float)) and isinstance(opp_max_pts, (int, float)):
            if max_pts > opp_max_pts:
                color = 'text-green-400'
            elif max_pts < opp_max_pts:
                color = 'text-red-400'
            else:
                color = 'text-yellow-400'
        return f'<td class="border px-2 py-1 text-center {color} {bg}">{max_pts:.2f}</td>'

    def summary(self, matchups):
        total = sum(m.get("max_points", 0) for m in matchups)
        return f"{total:.2f}"


class EfficiencyTable(TableConfig):
    title = "⚡ Weekly Lineup Efficiency"
    summary_header = "Avg %"

    def cell(self, team, week_idx, matchup, bg=""):
        points = matchup.get("points_for", 0)
        max_pts = matchup.get("max_points", 0)
        if max_pts > 0:
            pct = points / max_pts * 100
            color = 'text-green-400' if pct >= 90 else 'text-yellow-400' if pct >= 75 else 'text-red-400'
            display = f"{pct:.1f}%"
        else:
            color = 'text-gray-400'
            display = "-"
        return f'<td class="border px-2 py-1 text-center {color} {bg}">{display}</td>'

    def summary(self, matchups):
        valid = [(m.get("points_for", 0), m.get("max_points", 0))
                 for m in matchups if m.get("max_points", 0) > 0]
        if not valid:
            return "-"
        avg = sum(p / mx * 100 for p, mx in valid) / len(valid)
        color = 'text-green-400' if avg >= 90 else 'text-yellow-400' if avg >= 75 else 'text-red-400'
        return f'<span class="{color}">{avg:.1f}%</span>'


class PointsLeftTable(TableConfig):
    title = "💸 Weekly Points Left on Bench"
    summary_header = "Total"

    def cell(self, team, week_idx, matchup, bg=""):
        left = matchup.get("max_points", 0) - matchup.get("points_for", 0)
        color = 'text-red-400' if left > 30 else 'text-yellow-400' if left > 15 else 'text-green-400'
        return f'<td class="border px-2 py-1 text-center {color} {bg}">{left:.2f}</td>'

    def summary(self, matchups):
        total = sum(m.get("max_points", 0) - m.get("points_for", 0) for m in matchups)
        return f"{total:.2f}"