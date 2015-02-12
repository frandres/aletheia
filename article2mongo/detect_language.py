import unicodedata
from nltk.corpus import stopwords
spanish = stopwords.words('spanish')

catalan = [u'a', u'abans', u'aci', u'ah', u'aixi', u'aixo', u'al', u'als', u'aleshores', u'algun', u'alguna', u'algunes', u'alguns', u'alhora', u'alla', u'alli', u'allo', u'altra', u'altre', u'altres', u'amb', u'ambdos', u'ambdues', u'apa', u'aquell', u'aquella', u'aquelles', u'aquells', u'aquest', u'aquesta', u'aquestes', u'aquests', u'aqui', u'baix', u'cada', u'cadascu', u'cadascuna', u'cadascunes', u'cadascuns', u'com', u'contra', u"d'un", u"d'una", u"d'unes", u"d'uns", u'dalt', u'de', u'del', u'dels', u'des', u'despres', u'dins', u'dintre', u'donat', u'doncs', u'durant', u'e', u'eh', u'el', u'els', u'em', u'en', u'encara', u'ens', u'entre', u'erem', u'eren', u'ereu', u'es', u'es', u'esta', u'esta', u'estavem', u'estaven', u'estaveu', u'esteu', u'et', u'etc', u'ets', u'fins', u'fora', u'gairebe', u'ha', u'han', u'has', u'havia', u'he', u'hem', u'heu', u'hi', u'ho', u'i', u'igual', u'iguals', u'ja', u"l'hi", u'la', u'les', u'li', u"li'n", u'llavors', u"m'he", u'ma', u'mal', u'malgrat', u'mateix', u'mateixa', u'mateixes', u'mateixos', u'me', u'mentre', u'mes', u'meu', u'meus', u'meva', u'meves', u'molt', u'molta', u'moltes', u'molts', u'mon', u'mons', u"n'he", u"n'hi", u'ne', u'ni', u'no', u'nogensmenys', u'nomes', u'nosaltres', u'nostra', u'nostre', u'nostres', u'o', u'oh', u'oi', u'on', u'pas', u'pel', u'pels', u'per', u'pero', u'perque', u'poc', u'poca', u'pocs', u'poques', u'potser', u'propi', u'qual', u'quals', u'quan', u'quant', u'que', u'que', u'quelcom', u'qui', u'quin', u'quina', u'quines', u'quins', u"s'ha", u"s'han", u'sa', u'semblant', u'semblants', u'ses', u'seu', u'seus', u'seva', u'seva', u'seves', u'si', u'sobre', u'sobretot', u'soc', u'solament', u'sols', u'son', u'son', u'sons', u'sota', u'sou', u"t'ha", u"t'han", u"t'he", u'ta', u'tal', u'tambe', u'tampoc', u'tan', u'tant', u'tanta', u'tantes', u'teu', u'teus', u'teva', u'teves', u'ton', u'tons', u'tot', u'tota', u'totes', u'tots', u'un', u'una', u'unes', u'uns', u'us', u'va', u'vaig', u'vam', u'van', u'vas', u'veu', u'vosaltres', u'vostra', u'vostre', u'vostres']


def det_language(text):
    spanish_counter = 0
    catalan_counter = 0
    for word in text.split(' '):
        if word in spanish:
            spanish_counter+=1
        if word in catalan:
            catalan_counter+=1

    return 'spanish' if spanish_counter>catalan_counter else 'catalan'
