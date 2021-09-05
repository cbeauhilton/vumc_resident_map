import json
import os
import sqlite3 as sql

# import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_html import HTMLSession


def get_one_page(url: str):

    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    r = session.get(url)
    rows = r.html.find("div.node--type-person")

    return soup, rows


def get_category(row, soup):
    category = ""
    id = row.attrs["data-history-node-id"]
    id_node = {"data-history-node-id": f"{id}"}
    cat_l = []
    for sib in soup.find("div", id_node).previous_siblings:
        s = str(sib).strip()
        if s:
            try:
                h = BeautifulSoup(s, "html.parser")
                cat_l.append(h.a["name"])
            except:
                pass
    if cat_l:
        category = "".join(cat_l).strip()

    return category


def get_name(row):
    name = row.find("div.field--name-node-title")[0].text.strip()
    return name


def get_hometown(row):
    hometown = (
        row.find("div.field--name-field-hometown")[0].text.split("\n")[-1].strip()
    )
    return hometown


def get_college(row):  # [-1]
    *_, college = row.find("div.field--name-field-resident-college")[0].text.split("\n")
    return college


def get_med_school(row):
    *_, med_school = row.find("div.field--name-field-education-1")[0].text.split("\n")
    return med_school


def get_career_plans(row):
    *_, career_plans = row.find("div.field--name-field-career-plans")[0].text.split(
        "\n"
    )
    # [-1]
    return career_plans


def get_bio(row):
    *_, bio = row.find("div.field--name-field-brief-description")[0].text.split("\n")
    # [-1]
    return bio


def get_img_popup(row, bio):
    root_url = "https://medicine.vumc.org"
    try:
        src = (
            root_url
            + row.find("div.field--name-field-barista-photo")[0]
            .find("img")[0]
            .attrs["src"]
        )
    except:
        src = ""
    try:
        href = (
            root_url
            + row.find("div.field--name-field-barista-photo")[0]
            .find("a")[0]
            .attrs["href"]
        )
    except:
        href = ""
    try:
        alt = (
            row.find("div.field--name-field-barista-photo")[0]
            .find("img")[0]
            .attrs["alt"]
        )
    except:
        alt = ""

    img_dict = {
        "img_src": f"{src}",
        "href": f"{href}",
        "alt": f"{alt}",
        "width": 100,
    }
    img_json = json.dumps(img_dict)

    popup_dict = {
        "image": src,
        "alt": alt,
        "title": alt,
        "description": bio,
        "link": href,
    }

    popup_json = json.dumps(popup_dict)

    return img_json, popup_json


def try_or(func, default=None, expected_exc=(Exception,)):
    try:
        return func()
    except expected_exc:
        return default


if __name__ == "__main__":

    session = HTMLSession(
        browser_args=[
            "--no-sandbox",
            "--user-agent=Mozilla/5.0 (Windows NT 5.1; rv:7.0.1) Gecko/20100101 Firefox/7.0.1",  # noqa
        ]
    )

    d = {}
    d["category"] = []
    d["name"] = []
    d["hometown"] = []
    d["college"] = []
    d["medicalschool"] = []
    d["careerplans"] = []
    d["bio"] = []
    d["img"] = []
    d["popup"] = []

    url = "https://medicine.vumc.org/people/current-internal-medicine-housestaff"
    soup, rows = get_one_page(url)

    for row in rows:

        j = {}
        j["name"] = try_or(lambda: get_name(row))
        j["hometown"] = try_or(lambda: get_hometown(row))
        j["category"] = try_or(lambda: get_category(row=row, soup=soup))
        j["college"] = try_or(lambda: get_college(row))
        j["medicalschool"] = try_or(lambda: get_med_school(row))
        j["careerplans"] = try_or(lambda: get_career_plans(row))
        bio = try_or(lambda: get_bio(row))
        if bio:
            j["bio"] = bio
            j["img"], j["popup"] = try_or(lambda: get_img_popup(row=row, bio=bio))

        u = "http://127.0.0.1:8000/residents/"
        db_response = requests.post(u, json=j)
        print(db_response.text)
