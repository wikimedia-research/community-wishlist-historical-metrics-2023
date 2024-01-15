# Community Wishlist Survey Historical Metrics 2023

The [Community Wishlist Survey](https://meta.wikimedia.org/wiki/Community_Wishlist_Survey) (hereinafter CWS) is an annual survey that allows contributors to the Wikimedia projects to propose and vote for tools and platform improvements. The survey had eight iterations since its inception in 2015, the last one being in 2023. The [Community Tech](https://www.mediawiki.org/wiki/Community_Tech) team usually handles the technical development of the selected wishes, along with running the survey itself. In some cases, wishes have also been completed by volunteers or staff from other teams with little to no input from the Community Tech team.

As of December 2023, the Community Tech is working on analysing the feedback and participation from previous years to understand how this process could be improved to keep up with the growing needs of the movement, referred to as the [Future of the Wishlist](https://meta.wikimedia.org/wiki/Community_Wishlist_Survey/Future_Of_The_Wishlist). The historical metrics analysis is intended to support this process by surfacing historical trends of survey. The majority of the report focuses on community participation i.e. who have been participating, where the users come from (home wiki), their experience level etc.

- Report: https://w.wiki/8ELx
- Appendix: https://w.wiki/8qya

----

## Repo file information

| File/folder                                                                                                                                    | Description                                                                                                                                                          |
|------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `archive/`                                                                                                                                     | initial exploratory analyses.                                                                                                                                        |
| `charts/`                                                                                                                                       | file outputs of charts generated during the analysis and used in the report.                                                                                         |
| `data/`                                                                                                                                         | non-sensitive structured datasets created during the analysis (proposals, usernames, page links, implementation).                                                               |
| `00_data_gathering_functions.py`                                                                                                               | contains various data gathering functions to extract data related proposals and participants, used across various notebooks.                                         |
| `01-wishes_data_gathering.ipynb`                                                                                                               | for each iteration of the survey, gather data related to categories, proposals, usernames of proposers, discussants, and voters, and rejection reasons, if any.      |
| `02-user_data_gathering.ipynb`                                                                                                                 | for each username, gather data on home-wiki, edit buckets on home-wiki and Meta-Wki, user rights on home-wiki and user account age.                                  |
| `03-data_modelling.ipynb`                                                                                                                      | model the proposals and user data gathered into various tables to be used during analysis, using [DuckDB](https://duckdb.org/).                                       |
| `04-analysis.ipynb`<br>➤ [view on nbviewer](https://nbviewer.org/github/wikimedia-research/cws-historical-metrics/blob/main/04-analysis.ipynb) | final analysis notebook _(note: the notebook intended to serve as a report, please refer to the [report on Meta-Wiki](https://w.wiki/8ELx) for narrative explanation and insights from the analysis)_ |
