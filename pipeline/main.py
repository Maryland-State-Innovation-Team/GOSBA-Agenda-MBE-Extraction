from modules.download_agendas import download_agendas_from_html_input
from modules.extract_agenda_structured import extract_agenda_structured

if __name__ == "__main__":
    # for year in range(2020, 2026):
    #     download_agendas_from_html_input(year)
    extract_agenda_structured()
