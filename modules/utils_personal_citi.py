def obtener_personal_citi(localidad):

    seguimiento_citi_qro = [
        "ALVARADO LEON CARINA LUZ",
        "CARRERA HERNANDEZ ERNESTO MICHELLE",
        "ARGUELLO CASTRO LUIS GUILLERMO",
        "MARTINEZ FRANCISCO JAVIER",
        "RAMIREZ OSCAR ALBERTO",
        "WALKTROUGHT",
    ]

    seguimiento_citi_tult = [
        "BERENICE PIEDAD FLORESZ",
        "POLETH JIMENEZ GONZALEZ",
        "DANIEL MORALES",
        "ERICK L. LUCIANNO",
        "JAVIER REYES NAVARRETE",
        "WALKTROUGHT",
    ]

    if localidad.upper() == "QUERETARO":
        return seguimiento_citi_qro

    if localidad.upper() == "TULTITLAN":
        return seguimiento_citi_tult

    return []
