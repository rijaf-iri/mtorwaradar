import csv


def readPointsCoords(file_csv):
    with open(file_csv) as file:
        csv_reader = csv.reader(file, delimiter=",")

        points = []
        firstrow = True
        for row in csv_reader:
            if firstrow:
                firstrow = False
                continue

            pts = {"id": row[0], "longitude": float(row[1]), "latitude": float(row[2])}
            points = points + [pts]

    return points
