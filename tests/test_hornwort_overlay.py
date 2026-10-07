import os


def test_hornwort_pine_tree_silhouette_and_surface_crawl():
    with open("ohverlay-hornwort.html", encoding="utf-8") as f:
        src = f.read()
    # Verifies pine-tree starburst needle whorls, single root system, and surface creeping
    assert "Dense Pine Starburst Whorls" in src
    assert "Pine-tree conical profile" in src
    assert "Single unified root origin" in src
    assert "topLength + shape.horizontal" in src
