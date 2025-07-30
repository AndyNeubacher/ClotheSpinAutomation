import cv2
import numpy as np

def detect_clothespin(frame):
    """
    Erkennt die Kontur einer Wäscheklammer im gegebenen Frame und berechnet
    ihren Mittelpunkt und ihre Rotation.
    """
    # 1. Graustufenkonvertierung
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2. Rauschunterdrückung (Gaußscher Weichzeichner)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Schwellenwertbildung (Otsu's Binarisierung ist oft gut)
    # Versuchen Sie, einen Schwellenwert zu finden, der die Wäscheklammer gut isoliert.
    # Hier wird Otsu's Methode verwendet, die den Schwellenwert automatisch bestimmt.
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Optional: Morphologische Operationen, um kleine Löcher zu schließen oder Objekte zu trennen
    # kernel = np.ones((3,3),np.uint8)
    # thresh = cv2.erode(thresh, kernel, iterations = 1)
    # thresh = cv2.dilate(thresh, kernel, iterations = 1)

    # 4. Konturerkennung
    # RETR_EXTERNAL holt nur die äußeren Konturen
    # CHAIN_APPROX_SIMPLE komprimiert horizontale, vertikale und diagonale Segmente und speichert nur ihre Endpunkte.
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    clothespin_contour = None
    max_area = 0
    # 5. Konturen filtern (Beispiel: größte Kontur finden, die einer Wäscheklammer ähnelt)
    # Hier nehmen wir an, die Wäscheklammer ist das größte Objekt.
    # Sie müssen diesen Filter an Ihre spezifische Wäscheklammer und Umgebung anpassen.
    for contour in contours:
        area = cv2.contourArea(contour)
        # Filtern nach Mindestgröße, um kleines Rauschen zu ignorieren
        if area > 1000:  # Passen Sie diesen Wert an Ihre Wäscheklammergröße an
            # Optional: Überprüfen des Verhältnisses von Breite zu Höhe (Aspect Ratio)
            # x, y, w, h = cv2.boundingRect(contour)
            # aspect_ratio = float(w)/h
            # if 0.5 < aspect_ratio < 2.0: # Beispielwerte für eine Wäscheklammer

            if area > max_area:
                max_area = area
                clothespin_contour = contour

    if clothespin_contour is not None:
        # 6. Berechnung von Mittelpunkt und Rotation
        # Mittelpunkt (Moment)
        M = cv2.moments(clothespin_contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
        else:
            cX, cY = 0, 0

        # Orientierung (Rotated Bounding Box)
        # Diese Box ist an die Kontur angepasst und gibt den Winkel.
        rect = cv2.minAreaRect(clothespin_contour)
        ((x, y), (width, height), angle) = rect

        # Anpassen des Winkels: minAreaRect gibt einen Winkel zwischen -90 und 0 Grad oder 0 und 90 Grad zurück,
        # abhängig von der Ausrichtung des Rechtecks. Möglicherweise müssen Sie ihn normalisieren.
        # Wenn die Breite größer als die Höhe ist, ist der Winkel der Winkel der Breite zur x-Achse.
        # Wenn die Höhe größer als die Breite ist, ist der Winkel 90 Grad plus der Winkel der Höhe zur x-Achse.
        if width < height:
            angle = angle + 90

        box = cv2.boxPoints(rect)
        box = np.int0(box)

        # 7. Visualisierung
        cv2.drawContours(frame, [box], 0, (0, 255, 0), 2) # Rotierte Bounding Box
        cv2.circle(frame, (cX, cY), 7, (255, 0, 0), -1) # Mittelpunkt (Blau)
        cv2.putText(frame, f"Mittelpunkt: ({cX}, {cY})", (cX + 10, cY + 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        cv2.putText(frame, f"Winkel: {angle:.2f} Grad", (cX + 10, cY + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    return frame, clothespin_contour, (cX, cY) if clothespin_contour is not None else None, angle if clothespin_contour is not None else None

def main():
    cap = cv2.VideoCapture(0) # 0 ist die Standard-Webcam. Ändern Sie dies bei Bedarf.

    if not cap.isOpened():
        print("Fehler: Kamera konnte nicht geöffnet werden.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Fehler: Kann kein Frame empfangen (Stream-Ende?). Exiting ...")
            break

        processed_frame, clothespin_contour, center, angle = detect_clothespin(frame.copy())

        cv2.imshow('Wäscheklammer-Erkennung', processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()