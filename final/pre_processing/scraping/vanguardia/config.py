base_path = './articulos_por_secciones/'

global_path = base_path+'global/'
comarcas_path = base_path+'comarcas/'

def get_folder(section_name):
    return sections[section_name]['folder']

def get_index_builder(section_name):
    return sections[section_name]['index_builder']

pirineos = {'folder':comarcas_path+'pirineos/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54333755763']}

barcelones_nord = {'folder':comarcas_path+'barcelones-nord/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54247363778']}

bergueda = {'folder':comarcas_path+'bergueda/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54333021090']}

valles_oriental = {'folder':comarcas_path+'valle-oriental/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54247363396']}

anoia = {'folder':comarcas_path+'anoia/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54247363667']}

baix_llobregat = {'folder':comarcas_path+'baix-llobregat/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54247363617']}

bagues = {'folder':comarcas_path+'bagues/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54247363639']}

maresme = {'folder':comarcas_path+'maresme/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54235563653']}

reus = {'folder':comarcas_path+'reus/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54365578319']}

sabadell = {'folder':comarcas_path+'sabadell/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54365577915']}

solsones = {'folder':comarcas_path+'solsones/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54333755731']}

terrassa = {'folder':comarcas_path+'terrassa/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54365577955']}

osona = {'folder':comarcas_path+'osona/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54333755717']}

terres_de_l_ebre = {'folder':comarcas_path+'terres-de-l-ebre/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54333021125']}

vilafranca = {'folder':comarcas_path+'vilafranca/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54365578031']}

vilanova = {'folder':comarcas_path+'vilanova/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54365578280']}

opinion_director = {'folder': global_path+'opinion-director/',
                    'index_builder' : ['http://www.lavanguardia.com/opinion/articulos-director/lista/index.html?numPage=','']}

politica = {'folder': global_path+'politica/',
            'index_builder' : ['http://www.lavanguardia.com/noticias-por-seccion/lista/index.html?numPage=','&categorization=54028875383']}

sections = {'pirineos':pirineos, 'barcelones-nord':barcelones_nord,'bergueda':bergueda,'valles-oriental':valles_oriental,'anoia':anoia,'baix-llobregat':baix_llobregat,'bagues':bagues,'maresme':maresme,'reus':reus,'sabadell':sabadell,'solsones':solsones,'terrassa':terrassa,'osona':osona,'terres-de-l-ebre':terres_de_l_ebre,'vilafranca':vilafranca, 'vilanova':vilanova,'opinion-director':opinion_director,'politica':politica}
