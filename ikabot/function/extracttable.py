from bs4 import BeautifulSoup


def parse_table(html):
    soup = BeautifulSoup(html, "html.parser")

    # Find the table with the class 'embassyTable'
    table = soup.find("table", class_="embassyTable")

    # Check if the table is found
    if not table:
        return []
    # Extract table headers
    headers = [th.text.strip() for th in table.find_all("th")]

    # Extract table rows
    rows = []
    for tr in table.find_all("tr"):
        row = [td.text.strip() for td in tr.find_all("td")]
        if row:  # Check if the row is not empty
            # Join and clean the "Alliance member" column
            row[4] = " ".join(row[4].split())

            # Extract the end date from the script element
            script_tag = tr.find("script")
            if script_tag:
                end_date = script_tag.text.split("enddate: ")[1].split(",")[0]
                row.append(end_date)

            rows.append(row)

    # Combine headers and rows into a list of arrays
    militaryMovements = [headers + ["End Date"]] + rows

    # Print the militaryMovements
    result = []
    for movement in militaryMovements[1:]:
        attacker_name, attacker_city_raw = movement[3].split("\n")
        attacker_city_name = attacker_city_raw[1:-1].strip()
        ally_name, ally_city_name_raw = movement[4].split("(")
        ally_city_name = ally_city_name_raw[0:-1].strip()
        result.append(
            {
                "period": movement[0],
                "active_action": movement[1],
                "units": movement[2],
                "attacker_name": attacker_name,
                "attacker_city_name": attacker_city_name,
                "ally_name": ally_name,
                "ally_city_name": ally_city_name,
                "end_date": movement[5],
            }
        )

    return result
