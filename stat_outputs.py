def generate_html(matchups_by_team, season_stats, enriched_starters, writeups):
    sections = []
    sections.append(generate_head())
    sections.append(generate_nav(writeups))
    sections.append(generate_matchup_tables(matchups_by_team))
    sections.append(generate_summary_tables(season_stats))
    sections.append(generate_writeup_sections(writeups, enriched_starters))
    sections.append(generate_footer())
    
    return f"""<!DOCTYPE html>
<html lang="en">
{chr(10).join(sections)}
</html>"""

def generate_head():
    return '''<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decadent Dozen - Dynasty League 2025 Recap</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {
            background-color: #1a1a1a;
            color: #e5e5e5;
        }

        html {
            scroll-behavior: smooth;
        }
    </style>
    <script>
        document.addEventListener("DOMContentLoaded", () => {
            document.querySelectorAll("table.sortable").forEach((table) => {
                const headers = table.querySelectorAll("th");

                headers.forEach((th, index) => {
                    th.addEventListener("click", () => {
                        const rows = Array.from(table.querySelectorAll("tbody tr"));
                        const getValue = row => row.cells[index].innerText.trim();

                        let sorted = rows.sort((a, b) => {
                            const va = getValue(a), vb = getValue(b);
                            const na = parseFloat(va), nb = parseFloat(vb);
                            return isNaN(na) || isNaN(nb) ? va.localeCompare(vb) : na - nb;
                        });

                        const asc = !th.classList.contains("asc");

                        // Reset all headers in this table
                        headers.forEach(h => {
                            h.classList.remove("asc", "desc");
                            const icon = h.querySelector(".sort-indicator");
                            if (icon) icon.textContent = "";
                        });

                        // Update clicked header
                        th.classList.add(asc ? "asc" : "desc");
                        const icon = th.querySelector(".sort-indicator");
                        if (icon) icon.textContent = asc ? "▲" : "▼";

                        if (!asc) sorted.reverse();

                        // Highlight sorted column
                        table.querySelectorAll("tbody tr").forEach(row => {
                            row.querySelectorAll("td").forEach((td, i) => {
                                td.classList.toggle("font-bold", i === index);
                            });
                        });

                        sorted.forEach(row => table.querySelector("tbody").appendChild(row));
                    });
                });
            });
        });
    </script>
</head>'''

def generate_footer():
    return '''<script>
        function toggleMore(button) {
            const contentId = button.getAttribute('data-target');
            const moreContent = document.getElementById(contentId);
            moreContent.classList.toggle('hidden');
            const isHidden = moreContent.classList.contains('hidden');
            
            document.querySelectorAll(`[data-target="${contentId}"]`).forEach(btn => {
                btn.textContent = isHidden ? 'Show more' : 'Hide';
            });
        }
    </script>
</body>'''

def generate_nav(writeups):
    links = []
    for section in writeups["sections"]:
        for team in section["teams"]:
            links.append(f'<li><a href="#{team["id"]}">{team["display"]}</a></li>\n')
    
    return f'''<body class="px-4 py-6 max-w-screen-md mx-auto">
    <header class="text-center mb-6">
        <h1 class="text-3xl font-bold">Decadent Dozen - 2025 Recap</h1>
        <p class="text-gray-400">A look back at the season's stats and insights</p>
    </header>
    
    <nav class="mb-6 sticky top-0 bg-[#1a1a1a] z-10 py-2 border-b border-gray-700">
        <h2 class="font-semibold mb-2">Jump to Team</h2>
        <ul class="flex flex-wrap gap-3 text-blue-400 text-sm">
            {''.join(links)}
        </ul>
    </nav>'''


def generate_matchup_tables(matchups_by_team):
    weeks = len(next(iter(matchups_by_team.values())))

    bg_classes = [
        "bg-blue-900/30",
        "bg-amber-800/30",
        "bg-purple-800/30",
        "bg-lime-800/30",
        "bg-rose-800/30",
        "bg-cyan-800/30"
    ]

    matchup_colors_by_week = [{} for _ in range(weeks)]
    for week_idx in range(weeks):
        used_pairs = set()
        color_idx = 0
        for team, matchups in matchups_by_team.items():
            opp = matchups[week_idx]['opp']
            pair = tuple(sorted((team, opp)))
            if pair not in used_pairs:
                used_pairs.add(pair)
                matchup_colors_by_week[week_idx][pair] = bg_classes[color_idx % len(bg_classes)]
                color_idx += 1

    def build_table(title, cell_func):
        html = [f'<h2 class="text-xl font-bold mt-4 mb-4">{title}</h2>']
        html.append('<table class="table-auto border-collapse text-sm mb-4">')
        html.append('<thead><tr><th class="border px-2 py-1 text-left">Team</th>')
        for week in range(1, weeks + 1):
            html.append(f'<th class="border px-2 py-1">{week}</th>')
        html.append('</tr></thead><tbody>')

        for team, matchups in matchups_by_team.items():
            html.append(f'<tr><td class="border px-2 py-1">{team}</td>')
            for week_idx, matchup in enumerate(matchups):
                html.append(cell_func(team, week_idx, matchup))
            html.append('</tr>')

        html.append('</tbody></table>')
        return '\n'.join(html)

    def wl_cell(team, week_idx, matchup):
        result = matchup.get("result", "-")
        opp = matchup.get("opp", "")
        pair = tuple(sorted((team, opp)))
        bg = matchup_colors_by_week[week_idx].get(pair, "")
        color = {
            'W': 'text-green-400',
            'L': 'text-red-400',
            'D': 'text-yellow-400',
            '-': 'text-gray-400'
        }.get(result, '')
        return f'<td class="border px-2 py-1 {color} {bg}">{result}</td>'
    
    def margin_cell(team, week_idx, matchup):
        margin = matchup.get("margin", 0)
        opp = matchup.get("opp", "")
        pair = tuple(sorted((team, opp)))
        bg = matchup_colors_by_week[week_idx].get(pair, "")
        if isinstance(margin, (int, float)):
            if margin > 0:
                color = 'text-green-400'
                display = f"+{margin:.2f}"
            elif margin < 0:
                color = 'text-red-400'
                display = f"{margin:.2f}"
            else:
                color = 'text-yellow-400'
                display = "0.00"
        else:
            color = 'text-gray-400'
            display = "-"
        return f'<td class="border px-2 py-1 {color} {bg}">{display}</td>'

    def points_cell(team, week_idx, matchup):
        points = matchup.get("points_for", 0)
        opp = matchup.get("opp", "")
        opp_points = matchup.get("points_against", 0)
        pair = tuple(sorted((team, opp)))
        bg = matchup_colors_by_week[week_idx].get(pair, "")
        color = ''
        if isinstance(points, (int, float)) and isinstance(opp_points, (int, float)):
            if points > opp_points:
                color = 'text-green-400'
            elif points < opp_points:
                color = 'text-red-400'
            else:
                color = 'text-yellow-400'
        return f'<td class="border px-2 py-1 {color} {bg}">{points}</td>'
    
    html = [
        '<div class="w-screen px-4 -ml-4">',
        '<section class="overflow-x-auto px-2">'
    ]
    html.append(build_table("📊 Weekly Win/Loss Results", wl_cell))
    html.append('<p class="text-sm text-gray-400 mb-16">Background colors match teams that played each other that week.</p>')
    html.append(build_table("📈 Weekly Points Scored", points_cell))
    html.append('<p class="text-sm text-gray-400 mb-16">Background colors match teams that played each other that week.</p>')
    html.append(build_table("📉 Weekly Point Differentials", margin_cell))
    html.append('<p class="text-sm text-gray-400 mb-16">Positive values indicate a win. Negative values indicate a loss. ' \
    'Background colors match teams that played each other that week.</p>')
    html.append('</section></div>')
    return '\n'.join(html)


def generate_writeup_sections(writeups, enriched_starters):
    html = []
    for section in writeups["sections"]:
        html.append(f'<h2 class="text-2xl font-bold mt-8 mb-4">{section["title"]}</h2>')
        for team in section["teams"]:
            html.append(generate_team_section(team, enriched_starters))
    return '\n'.join(html)

def generate_team_section(team, enriched_starters):
    more_paragraphs = ''.join(f'<p>\n\t{p}\n</p>' for p in team["more"])
    starter_table = generate_team_starter_table(
        enriched_starters.get(team["sleeper_username"], [])
    )
    
    return f'''<div>
        <h3 class="text-xl font-semibold scroll-mt-28 md:scroll-mt-20" id="{team["id"]}">
            {team["emoji"]} - @{team["sleeper_username"]} ({team["display"]}) - {team["team_name"]} - ({team["record"]})
        </h3>
        <div class="space-y-2 ml-6 mr-6 mt-2">
            <p>{team["blurb"]}</p>
            <div class="hidden more-content space-y-2" id="more-{team["id"]}">
                {more_paragraphs}
                <button class="text-blue-400 text-sm" data-target="more-{team["id"]}" onclick="toggleMore(this)">Show more</button>
                {starter_table}
            </div>
            <button class="text-blue-400 text-sm" data-target="more-{team["id"]}" onclick="toggleMore(this)">Show more</button>
        </div>
    </div>'''


def generate_team_starter_table(players):
    html = ['<div class="mt-6 pt-4 border-t border-gray-700">']
    html.append('<h4 class="text-base font-semibold mb-3 text-gray-300">🏈 Player Stats</h4>')
    html.append('<table class="sortable table-auto border-collapse text-sm mb-2 w-full">')
    html.append('''<thead><tr>
        <th class="border px-2 py-1 text-left cursor-pointer hover:underline">Player <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">Pos <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">NFL Team <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">Age <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">Exp <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">Games Played <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">Starts <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">Pts in Starts <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">PPG Started <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">Total Pts <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">PPG <span class="sort-indicator"></span></th>
        <th class="border px-2 py-1 cursor-pointer hover:underline">PPG Diff. When Started <span class="sort-indicator"></span></th>
    </tr></thead><tbody>''')

    for p in players:
        img = f'https://sleepercdn.com/content/nfl/players/thumb/{p["id"]}.jpg'
        exp = "R" if p["years_exp"] == 0 else f'{p["years_exp"]}yr'
        html.append(f'''<tr>
            <td class="border px-2 py-1" title="{p["name"]}">
                <div class="flex items-center gap-2 overflow-hidden">
                    <img src="{img}" onerror="this.style.display='none'"
                         class="w-8 h-8 rounded-full object-cover" />
                    <span class="truncate">{p["name"]}</span>
                </div>
            </td>
            <td class="border px-2 py-1 text-center">{p["position"]}</td>
            <td class="border px-2 py-1 text-center">{p["nfl_team"]}</td>
            <td class="border px-2 py-1 text-center">{p["age"]}</td>
            <td class="border px-2 py-1 text-center">{exp}</td>
            <td class="border px-2 py-1 text-center">{p["games_played"]}</td>
            <td class="border px-2 py-1 text-center">{p["starts"]}</td>
            <td class="border px-2 py-1 text-center">{p["start_points"]}</td>
            <td class="border px-2 py-1 text-center">{p["ppgs"]}</td>
            <td class="border px-2 py-1 text-center">{p["total_points"]}</td>
            <td class="border px-2 py-1 text-center">{p["ppg"]}</td>
            <td class="border px-2 py-1 text-center">{p["ppg_diff"]}</td>
        </tr>''')

    html.append('</tbody></table>')
    html.append('</div>')
    return '\n'.join(html)

def generate_summary_tables(season_stats_by_team):
    general_keys = [
        "wins", "losses", "win %", "points_for", "points_for_normalized", 
        "points_against", "points_against_normalized"
    ]

    sos_keys = [
        "opp win %", "opp opp win %", "win % sos", "opp_points",
        "opp_points_normalized", "points_against_normalized", "luck_factor"
    ]

    key_name_mappings = {
        "wins": "Wins",
        "losses": "Losses",
        "win %": "Win %",
        "points_for": "Points For",
        "points_for_normalized": "PF Normalized",
        "points_against": "Points Against",
        "points_against_normalized": "PA Normalized",
        "opp win %": "Opponents' Win %",
        "opp opp win %": "Opps' Opps' Win %",
        "win % sos": "BCS Style SoS",
        "opp_points": "Opponents' Points",
        "opp_points_normalized": "OP Normalized",
        "luck_factor": "Luck Factor"
    }

    def build_table(title, keys):
        # Compute min/max for heatmap coloring
        min_max = {
            k: (min(stats.get(k, 0) for stats in season_stats_by_team.values()),
                max(stats.get(k, 0) for stats in season_stats_by_team.values()))
            for k in keys
        }

        color_classes = [
            "bg-red-900/40",
            "bg-orange-700/40",
            "bg-yellow-600/40",
            "bg-lime-600/40",
            "bg-green-500/40"
        ]

        html = [f'<h2 class="text-xl font-bold mt-4 mb-4">{title}</h2>']
        html.append('<table class="sortable table-auto border-collapse text-sm mb-4">')
        html.append('<thead><tr><th class="border px-2 py-1 text-left">Team</th>')
        for k in keys:
            html.append(f'<th class="border px-2 py-1 text-left cursor-pointer hover:underline">{key_name_mappings[k]} <span class="sort-indicator"></span></th>')
        html.append('</tr></thead><tbody>')

        for team, stats in season_stats_by_team.items():
            html.append(f'<tr><td class="border px-2 py-1">{team}</td>')
            for k in keys:
                val = stats.get(k, 0)
                num = val
                if isinstance(val, float):
                    val = f"{val:.2f}"
                min_val, max_val = min_max[k]
                norm = 0 if max_val == min_val else (num - min_val) / (max_val - min_val)
                idx = min(int(norm * (len(color_classes) - 1)), len(color_classes) - 1)
                bg = color_classes[idx]
                html.append(f'<td class="border px-2 py-1 {bg}">{val}</td>')
            html.append('</tr>')

        html.append('</tbody></table>')
        return ''.join(html)

    html = [
        '<div class="w-screen px-4 -ml-4">',
        '<section class="overflow-x-auto px-2">'
    ]
    html.append(build_table("🧮 General Stats", general_keys))
    html.append('<p class="text-sm text-gray-400 mb-16">Normalized values are percentage based relative to league averages.</p>')
    html.append(build_table("📅 Strength of Schedule Stats", sos_keys))
    html.append('<p class="text-sm text-gray-400">Opponents\' wins and points exclude games played against the team being analyzed.</p>')
    html.append('<p class="text-sm text-gray-400 mb-16">Luck Factor is the difference between the points scored against the team and the points opponents scored against other teams (both normalized)</p>')
    html.append('</section></div>')
    return ''.join(html)


def inject_overview_tables(index_path, table_html):
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    start = html.find("<!-- MATCHUP_TABLES_START -->")
    end = html.find("<!-- MATCHUP_TABLES_END -->")

    if start == -1 or end == -1:
        raise ValueError("Could not find MATCHUP_TABLES markers in HTML")

    new_html = (
        html[:start + len("<!-- MATCHUP_TABLES_START -->")] +
        "\n" + table_html + "\n" +
        html[end:]
    )

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

def inject_starter_tables(index_path, enriched_starters):
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    for sleeper_username, team_players in enriched_starters.items():
        start_marker = f"<!-- STARTER_TABLE_START:{sleeper_username} -->"
        end_marker = f"<!-- STARTER_TABLE_END:{sleeper_username} -->"

        start = html.find(start_marker)
        end = html.find(end_marker)

        if start == -1 or end == -1:
            print(f"Warning: markers not found for {sleeper_username}, skipping.")
            continue

        # enriched_starters is keyed by display_name; match via sleeper_username
        team_players = enriched_starters.get(sleeper_username)
        if team_players is None:
            print(f"Warning: no starter data found for {sleeper_username}, skipping.")
            continue

        table_html = generate_team_starter_table(team_players)
        html = (
            html[:start + len(start_marker)] +
            "\n" + table_html + "\n" +
            html[end:]
        )

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)