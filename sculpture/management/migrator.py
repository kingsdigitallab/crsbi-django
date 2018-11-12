# -*- coding: utf-8
"""Module and base class for migrating legacy data.

Provides common data massage methods."""

import re

import sculpture.constants
import sculpture.management.migration_utils as migration_utils


class Migrator (object):

    def _massage_contributor_name (self, name):
        if name in ('Jill A Franklin', 'Jill A. Franklin'):
            name = 'Jill Franklin'
        elif name in ('H. Sunley', 'H.Sunley', 'H Sunley'):
            name = 'Harry Sunley'
        elif name in ('H Bodenham', 'H. J. Bodenham', 'H J Bodenham',
                      'H. J.Bodenham', 'H.J. Bodenham', 'H.J.Bodenham'):
            name = 'Harry Bodenham'
        elif name in ('G L Pearson', 'GL Pearson'):
            name = 'G. L. Pearson'
        elif name in ('G. Zarnecki',):
            name = 'George Zarnecki'
        elif name in ('Kathryn A Morrison', 'Kathryn A. Morrison'):
            name = 'Kathryn Morrison'
        elif name in ('Rita Wood (photography John McElheran', 'Rita Wood)'):
            name = 'Rita Wood'
        elif name in ('Ronald Baxter', 'Ron Baxter Date',):
            name = 'Ron Baxter'
        elif name in ('Simon C Kirsop'):
            name = 'Simon Kirsop'
        elif name == 'Thomas E Russo':
            name = 'Thomas E. Russo'
        return name

    def _massage_country_name (self, name):
        if self._site_id.startswith('id'):
            name = 'Republic of Ireland'
        elif self._site_id.startswith('ni'):
            name = 'Northern Ireland'
        else:
            name = 'England'
        return name

    def _massage_dedication_name (self, name, period):
        if not name:
            name = None
        elif name == 'Abbey of the Blessed Virgin Mary':
            name = 'Blessed Virgin Mary'
        elif name == 'Assumption of the Blessed Vrigin Mary':
            name = 'Assumption of the Blessed Virgin Mary'
        elif name == 'Castleisland Church of Ireland graveyard':
            name = 'n/a'
        elif name == 'Jerpoint Abbey':
            name = 'St Mary'
        elif name == 'Lismore Castle Gateway':
            name = 'n/a'
        elif name in ('none', 'None'):
            name = None
        elif name == 'not applicable':
            name = 'n/a'
        elif name in ('not known', 'not recorded', 'no record', 'unknown', '?'):
            name = 'not confirmed'
        elif name == 'Nativity of Blessed Virgin Mary':
            name = 'Nativity of the Blessed Virgin Mary'
        elif name == u'St Brendan’s Cathedral':
            name = 'St Brendan'
        elif name == "St Briget's":
            name = 'St Briget'
        elif name == "St Brigid's":
            name = 'St Brigid'
        elif name == 'St. Edward':
            name = 'St Edward'
        elif name == 'St Fechin\'s Cathedral':
            name = 'St Fechin'
        elif name == u'St Finbarre’s Cathedral':
            name = 'St Finbarre'
        elif name == "St Flannan's 'oratory'":
            name = 'St Flannan'
        elif name in ('St Hohn the Baptist', 'St John Baptist'):
            name = 'St John the Baptist'
        elif name == 'St John Evangelist':
            name = 'St John the Evangelist'
        elif name in ('StMary', 'St mary', 'St Mary St Mary'):
            name = 'St Mary'
        elif name in ('St Mary-the-Virgin', 'St Mary The Virgin'):
            name = 'St Mary the Virgin'
        elif name in ('St Mary\'s Cathedral', u'St Mary’s Cathedral'):
            name = 'St Mary'
        elif name == "St Mary's church":
            name = 'St Mary'
        elif name == 'St Melangell St Melangell':
            name = 'St Melangell'
        elif name == 'St Michael and all Angels':
            name = 'St Michael and All Angels'
        elif name == "St Mogue's":
            name = 'St Mogue'
        elif name == "St Mo-Diomog's church":
            name = 'St Mo-Diomog'
        elif name in ('St Mogue\'s well', 'St Mogues well'):
            name = 'St Mogue'
        elif name == 'St Molaise\'s House':
            name = 'St Molaise'
        elif name == "St Munnu's":
            name = 'St Munnu'
        elif name == "St Peter's":
            name = 'St Peter'
        elif name == u'St Sciath\N{RIGHT SINGLE QUOTATION MARK}s':
            name = 'St Sciath'
        elif name == 'St Thomas A Becket':
            name = 'St Thomas a Becket'
        elif name == 'unconfirmed':
            name = 'not confirmed'
        # Special handling for St Thomas a Becket.
        if name == 'St Thomas a Becket' and \
           period.name == sculpture.constants.DATE_MEDIEVAL:
            name = 'St Thomas Becket'
        if name:
            name = name.replace('St. ', 'St ')
        return name

    def _massage_diocese_name (self, name, period):
        if name == 'Bath and Wells':
            name = 'Bath & Wells'
        elif name in ('Birmingham1919', 'Birmingham from 1929',
                    'Birmingham since 1905'):
            name = 'Birmingham'
        elif name == 'Bishopric of Exeter from 1072':
            name = 'Exeter'
        elif name == 'Chelmsford':
            name = 'Canterbury'
        elif name in ('Chester (from 1541)', 'Chester from 1541') and \
             period.name == sculpture.constants.DATE_NOW:
            name = 'Chester'
        elif name in ('Coventry and Lichfield', 'Coventry and Lichfield to 1836',
                      'Lichfield', 'Lichfield to 1075', 'Coventry',
                      'Lichfield to 1075, Chester to c.1086, Coventry and Lichfield to 1541',
                      'Lichfield (to 1075); Chester (to c.1086); Coventry and Lichfield (to 1541).') and \
            period.name == sculpture.constants.DATE_MEDIEVAL:
            name = 'Lichfield (to 1075); Chester (to c.1086); Coventry and Lichfield (to 1541)'
        elif name in ('Coventryuntil 1991', 'Coventy', 'Conventry'):
            name = 'Coventry'
        elif name == 'Derby since 1927':
            name = 'Derby'
        elif name in ('East Anglia', 'North Elmham c. 950-1071',
                      'North Elmham c.950-1071',
                      'North Elmham (c.950-1071), Thetford (1071-94), Norwich (from 1094') and \
             period.name == sculpture.constants.DATE_MEDIEVAL:
            name = 'North Elmham (c.950-1071), Thetford (1071-94), Norwich (from 1094)'
        elif name == 'Lichfield, Chester and Worcester' and \
             period.name == sculpture.constants.DATE_MEDIEVAL:
            name = 'Worcester'
        elif name in ('Lincoln', 'Lincloln', 'Lincoln to 1539',
                      'Lincoln to 1837', 'Lincolnto 1837', 'Dorchester/Lincoln') \
            and period.name == sculpture.constants.DATE_MEDIEVAL:
            name = 'Lincoln (Dorchester to 1085)'
        elif name == 'Lincloln':
            name = 'Lincoln'
        elif name == 'Llandaffto 1130s':
            name = 'Llandaff'
        elif name == 'London (to 1845), Rochester (to 1877)':
            name = 'London'
        elif name == 'Not known':
            name = 'not confirmed'
        elif name in ('Peterborough (from 1539)', 'Peterboroughfrom 1539',
                      'Peterborough from 1539') and \
             period.name == sculpture.constants.DATE_NOW:
            name = 'Peterborough'
        elif name in ('Ripon', 'Ripon and Leeds (diocese of Ripon renamed 1999)'):
            name = 'Ripon and Leeds'
        elif name in ('St Edmundsbury and Ipswich since 1914.',
                      'St Edmundsbury and Ipswich since 1914'):
            name = 'St Edmundsbury and Ipswich'
        elif name in ('Salisbury to 1404,', 'Salisbury Salisbury'):
            name = 'Salisbury'
        elif name == 'Southwell':
            name = 'Southwell and Nottingham'
        elif name in ('Worcester 1836-1918', 'Worcester from 1905',
                      'Worcester since 1990s'):
            name = 'Worcester'
        return name

    def _massage_feature_set_name (self, name):
        if name in ('Chancel arch/Apse archeses', 'Chancel arch/ Apse arch',
                    'Chancel/Apse arches', 'Apse/Chancel arches',
                    'Chancel /Apse arches', 'Chancel arch/ Apse arches',
                    'Chancel arche/Apse arches', 'Chancel arches/Apse arch',
                    'Chancel arch, apse arches', 'Chancel arch/Apse arches.',
                    'Chancel arch', 'Chancel/ Apse arches'):
            name = 'Chancel arch/Apse arches'
        elif name == 'Vaulting/Roof supports':
            name = 'Vaulting/Roof Supports'
        elif name == 'Piscinae/Pillar piscinae':
            name = 'Piscinae/Pillar Piscinae'
        elif name in ('Corbel Tables', 'Corbel Tables, Corbels',
                      'Corbel tables', 'Corbel Tables, corbels'):
            name = 'Corbel tables, corbels'
        elif name == 'Interior decoration':
            name = 'Interior Decoration'
        elif name in ('Stringcourses', 'String Courses', 'b. String Courses'):
            name = 'String courses'
        elif name in ('Tower/Transept Arches', 'Tower/ Transept arches',
                      'Tower/Transept arches.', 'Tower arch',
                      'Transept arches', 'Tower arches',
                      'Tower/Transept/Crossing arches',
                      'Tower arch/Transept/Crossing arches'):
            name = 'Tower/Transept arches'
        elif name == 'Clerestory':
            name = 'Clerestorey'
        elif name == 'Miscellaenous':
            name = 'Miscellaneous'
        elif name == 'Wall passage/Gallery arcades':
            name = 'Wall passages/Gallery arcades'
        return name

    def _massage_period_name (self, name):
        if not name:
            name = 'now'
        else:
            # Rework all variants of pre-1974.
            if name in ('pre- 1974', 'pre. 1974', 'pre_1974', 'pre-1874',
                        'pre 1974', 'pre-1974 warwickshire', 'pre-1974'):
                name = 'pre-1974 (traditional)'
            if name == 'medieval now':
                name = 'now'
            if name == 'medieval:':
                name = 'medieval'
        return name

    def _massage_region_name (self, name):
        if name == 'Derry (Northern Ireland)':
            name = 'Derry'
        elif name == 'Fermanagh (Northern Ireland)':
            name = 'Fermanagh'
        return name

    def _massage_settlement_name (self, name):
        if name == 'Abbey Church':
            name = 'Abbey church'
        elif name == 'Alien Priory Church, now English Heritage':
            name = 'Alien priory church'
        elif name in ('Augustinian Priory', 'Augustinian priory from 1189; parish church by 1302; briefly a friary church (1584)', 'Augustinian Priory, now owned by Norton Priory Museum Trust'):
            name = 'Augustinian priory'
        elif name == 'Barn (f parish church)':
            name = 'Barn, formerly parish church'
        elif name in ('Benedictine Abbey', 'Former Benedictine Abbey'):
            name == 'Benedictine abbey'
        elif name in ('Benedictine Priory church', 'Benedictine Priory originally, now part of the Farmland Museum', 'Former Benedictine Priory'):
            name = 'Benedictine priory'
        elif name == 'Casle':
            name = 'Castle'
        elif name == 'Chapel in castle':
            name = 'Castle chapel'
        elif name == 'Castle Gateway':
            name = 'Castle gateway'
        elif name in ('St Canice\'s Cathedral', 'Cathedral'):
            name = 'Cathedral church'
        elif name == 'Benedictine Abbey originally, now Cathedral':
            name = 'Cathedral, formerly Benedictine abbey'
        elif name == 'Benedictine monastery originally, now Cathedral':
            name = 'Cathedral, formerly Benedictine monastery'
        elif name in ('chapel originally, now Register Office',
                      'Chapel/Parish church',
                      'Former chapel, now farm outbuilding'):
            name = 'Chapel'
        elif name == 'Chapel of Ease':
            name = 'Chapel of ease'
        elif name == 'Originally the chapel of the Leper Hospital of St Mary Magdalene, now a chapel in the parish of Holy Cross':
            name = 'Chapel, formerly Leper Hospital Chapel'
        elif name in ('Chapel, formerly Parish church',
                      'Originally parish church, now chapel'):
            name = 'Chapel, formerly parish church'
        elif name == 'Originally a chapelry, now owned by the Orton Trust':
            name = 'Chapelry'
        elif name == 'Cistercian Abbey Church':
            name = 'Cistercian Abbey church'
        elif name == 'Former parish church, now a college library':
            name = 'College library, formerly parish church'
        elif name == 'Former corn-mill':
            name = 'Corn-mill'
        elif name in ('Deconsecrated church',
                      'Private chapel (?)(deconsecrated)'):
            name = 'Deconsecrated chapel'
        elif name == 'deconsecrated chapel (formerly Free Chapel)':
            name = 'Deconsecrated chapel, formerly Free Chapel'
        elif name in ('Parish church disused', 'Parish church, disused'):
            name = 'Disused parish church'
        elif name == 'Summer house folly':
            name = 'Folly'
        elif name == 'Formerly hospital chapel':
            name = 'Hospital chapel'
        elif name == 'formerly manor house, now hotel':
            name = 'Hotel, formerly manor house'
        elif name == 'Originally house of Augustinian canons':
            name = 'House of Augustinian canons'
        elif name == 'Manor House':
            name = 'Manor house'
        elif name == 'Monastic church and Priory complex, now in the care of English Heritage':
            name = 'Monastic church and priory complex'
        elif name == 'Mortuary Chapel':
            name = 'Mortuary chapel'
        elif name in ('Church', 'church', 'Former church, now parish room',
                      'Old parish church, rarely used', 'Paris Church',
                      'Parish chruch', 'Parish church (',
                      'Parish church and Music Centre',
                      'Parish church (benefice of Aldford and Bruera)',
                      'Parish church (benefice of Blisworth and Stoke Bruerne with Grafton Regis and Alderton)',
                      'Parish church (benefice of Brigstock with Stanion and Lowick and Sudborough)',
                      'Parish church (benefice of Daventry, Ashby St Ledgers, Braunston, Catesby, Hellidon, Staverton and Welton)',
                      'Parish church (benefice of Greens Norton with Bradden and Lichborough)',
                      'Parish church (benefice of Gretton with Rockingham and Cottingham with East Carlton)',
                      'Parish church (benefice of Isham with Pytchley)',
                      'Parish church (benefice of Pattishall with Cold Higham and Gayton with Tiffield)',
                      'Parish Church (benefice of Potterspury with Furtho and Yardley Gobion with Cosgrove and Wicken)',
                      'Parish church (benefice of Rothwell with Orton and Rushton with Glendon and Pipewell)',
                      'Parish church (benefice of Silverstone and Abthorpe with Slapton and Whittlebury and Paulerspury). Formerly a dependent chapel of Green\'s Norton',
                      'Parish church (benefice of Stoke Albany with Wilbarston and Ashley with Weston-by-Welland and Sutton Bassett)',
                      'Parish church (benefice of Tilston and Shocklach)',
                      'Parish church (benefice of Warmington, Tansor and Cotterstock and Fotheringhay and Southwick)',
                      'Parish church (benefice of West Haddon with Winwick and Ravensthorpe)',
                      'Parish church (Collegiate church to 1548)',
                      'Parish church, pilgrimage centre',
                      'Parish church (benefice of Geddington with Weekley)',
                      'Parish church to 1966'):
            name = 'Parish church'
        elif name == 'Former Benedictine Priory church, now parish church':
            name = 'Parish church, formerly Benedictine priory church'
        elif name == 'Parish church ex abbey':
            name = 'Parish church, formerly abbey'
        elif name in ('Formerly Augustinian priory, now parish church',
                      'Parish church (former Augustinian Priory)'):
            name = 'Parish church, formerly Augustinian priory'
        elif name in ('Benedictine Abbey, now parish church',
                      'Originally Benedictine Abbey, now parish church',
                      'Originally Benedictine Priory, now parish church'):
            name = 'Parish church, formerly Benedictine abbey'
        elif name == 'Bendictine Nunnery, now parish church':
            name = 'Parish church, formerly Benedictine nunnery'
        elif name in ('Formerly chapel, now parish church',
                      'Parish church (formerly a chapel of St Mary\'s, Oakley)',
                      'Parish church . Formerly a chapel of Stoke Edith',
                      'Parish church, formerly chapel'):
            name = 'Parish church, formerly chapel'
        elif name in ('Formerly Chapel of Ease, now parish church',
                      'Originally chapel of ease, now parish church',
                      'originally chapel of ease, now parish church',
                      'Chapel-of-ease to parish church'):
            name = 'Parish church, formerly chapel of ease'
        elif name == 'Originally chapelry, now parish church':
            name = 'Parish church, formerly chapelry'
        elif name == 'Parish church, originally a clas site':
            name = 'Parish church, formerly Clas site'
        elif name in ('Collegiate church, now parish church',
                      'Formerly Collegiate church, now parish church',
                      'Originally collegiate church, now parish church',
                      'Originally Collegiate church, then chapel, now parish church',
                      'Parish church (formerly collegiate church)'):
            name = 'Parish church, formerly collegiate church'
        elif name == 'Convent/Parish church':
            name = 'Parish church, formerly convent'
        elif name == 'Originally hospitium of Ramsey Abbey, now parish church':
            name = 'Parish church, formerly Hospitium of Ramsey Abbey'
        elif name == 'Originally Minster, now parish church':
            name = 'Parish church, formerly minster'
        elif name == 'Parish church, formerly Minster church':
            name == 'Parish church, formerly minster church'
        elif name == 'Monastic church (disused), Parish church by early 14thc':
            name = 'Parish church, formerly monastic church'
        elif name == 'Parish church, originally preceptory (?)':
            name = 'Parish church, formerly preceptory (?)'
        elif name == 'Premonstratensian Abbey, later, parish church':
            name = 'Parish church, formerly Premonstratensian abbey'
        elif name in ('Parish church, formerly part Priory Church',
                      'Priory, now parish church',
                      'Priory originally, now parish church'):
            name = 'Parish church, formerly priory church'
        elif name == 'Quasi-collegiate church in 12thc., now parish church':
            name = 'Parish church, formerly quasi-collegiate church'
        elif name == 'Parochial Church Chapel':
            name = 'Parochial church chapel'
        elif name in ('Private dwelling', 'Private home', 'Private residence'):
            name = 'Private house'
        elif name == 'Formerly parish church, now private house':
            name = 'Private house, formerly parish church'
        elif name == 'Public House':
            name = 'Public house'
        elif name in ('Church in care of Churches Conservation Trust',
                      'Parish church (redundant)', 'Redundant church',
                      'Redundant church (Redundant Churches Fund)'):
            name = 'Redundant parish church'
        elif name == 'Originally castle chapel, now Regimental chapel':
            name = 'Regimental chapel, formerly castle chapel'
        elif name == 'RC church':
            name = 'Roman Catholic church'
        elif name == 'Round Tower':
            name = 'Round tower'
        elif name in ('Abbey church ruin', 'Abbey Church (ruin)',
                      'Abbey ruins'):
            name = 'Ruined abbey church'
        elif name == 'Church and Abbey buildings (ruin), former Cistercian Abbey':
            name = 'Ruined abbey church and abbey buildings, formerly Cistercian abbey'
        elif name == 'Originally Augustinian Priory, then Abbey, now a ruin':
            name = 'Ruined Augustinian priory, formerly abbey'
        elif name == 'Cathedral (ruin)':
            name = 'Ruined cathedral'
        elif name == 'Former chapel of ease, now ruin':
            name = 'Ruined chapel of ease'
        elif name in ('Church (ruin)', 'Church ruins', 'church (ruin)'):
            name = 'Ruined church'
        elif name == 'Church (ruin) and round tower':
            name = 'Ruined church and round tower'
        elif name == 'Church of Ireland church (ruin)':
            name = 'Ruined Church of Ireland church'
        elif name == 'Church (ruin), former Arroasian Priory':
            name = 'Ruined church, formerly Arroasian priory'
        elif name in ('Church (ruin), former Augustinian Abbey',
                      'church (ruin), former Augustinian Abbey, on site of early monastery'):
            name = 'Ruined church, formerly Augustinian abbey'
        elif name == 'Church (ruin), former cathedral':
            name = 'Ruined church, formerly cathedral'
        elif name == 'Church (ruin), former cathedral':
            name = 'Ruined church, former cathedral'
        elif name == 'Monastic ruin':
            name = 'Ruined monastery'
        elif name in ('Church and enclosure (ruin)',
                      'Church and graveyard (ruin)',
                      'Former parish church (remains)', 'Ruined church'):
            name = 'Ruined parish church'
        elif name == 'Tower ruin':
            name = 'Ruined tower'
        elif name == 'School chapel (formerly chapel to the Hospital of St James and St John)':
            name = 'School chapel, formerly Hospital chapel'
        return name

    def _split_dedication (self, text):
        """Splits the text of a dedication into one or more actual
        dedications, each consisting of a tuple of name, date, and
        certainty.

        This method is to deal with names that are problematic with
        regards to date, certainty or multiplicity of names. The
        method _massage_dedication is also used subsequently to sort
        out typographic problems within a single name.

        """
        text = migration_utils.regularise_text(text)
        data = []
        if not text:
            pass
        elif text == 'All Saints and St Margaret':
            data.append(('All Saints', '', True))
            data.append(('St Margaret', '', True))
        elif text == 'All Saints (1419, Borthwick)':
            data.append(('All Saints', '1419, Borthwick', True))
        elif text == 'All Saints (1440, Prob. Reg.)':
            data.append(('All Saints', '1440, Prob. Reg.', True))
        elif text == 'All Saints (1508, Prob Reg. 8, f.14)':
            data.append(('All Saints', '1508, Prob Reg. 8, f.14', True))
        elif text == 'All Saints (1550, recorded at Borthwick)':
            data.append(('All Saints', '1550, recorded at Borthwick', True))
        elif text == 'Holy and Undivided Trinity and St Etheldreda':
            data.append(('Holy and Undivided Trinity', '', True))
            data.append(('St Etheldreda', '', True))
        elif text == 'Holy Trinity and St Mary':
            data.append(('Holy Trinity', '', True))
            data.append(('St Mary', '', True))
        elif text == 'Holy Trinity and St Oswald':
            data.append(('Holy Trinity', '', True))
            data.append(('St Oswald', '', True))
        elif text == 'Our Lady 16thc.':
            data.append(('Our Lady', '16thc.', True))
        elif text == 'Our Lady and the Holy Trinity':
            data.append(('Our Lady', '', True))
            data.append(('Holy Trinity', '', True))
        elif text == 'Saint Mary and St John the Evangelist':
            data.append(('St Mary', '', True))
            data.append(('St John the Evangelist', '', True))
        elif text == "Saints' Church (?)":
            data.append(("Saints' Church", '', False))
        elif re.search(r'^SS ([^ ]+) (and|&|with) ([^ ]+)$', text):
            match = re.search(r'^SS ([^ ]+) (and|&|with) ([^ ]+)$', text)
            data.append(('St ' + match.group(1), '', True))
            data.append(('St ' + match.group(3), '', True))
        elif re.search(r'^St\.? ([^ ]+) (and|&|with) St\.? ([^ ]+)$', text):
            match = re.search(r'^St\.? ([^ ]+) (and|&|with) St\.? ([^ ]+)$', text)
            data.append(('St ' + match.group(1), '', True))
            data.append(('St ' + match.group(3), '', True))
        elif text == 'SS Afran, Ieuan and Sannan':
            data.append(('St Afran', '', True))
            data.append(('St Ieuan', '', True))
            data.append(('St Sanna', '', True))
        elif text == 'SS Helen and John the Baptist':
            data.append(('St Helen', '', True))
            data.append(('St John the Baptist', '', True))
        elif text == 'SS John the Baptist and Alkmund':
            data.append(('St John the Baptist', '', True))
            data.append(('St Alkmund', '', True))
        elif text == 'SS. Peter and Paul':
            data.append(('St Peter', '', True))
            data.append(('St Paul', '', True))
        elif text == 'St Andrew (1529, Borthwick Institute)':
            data.append(('St Andrew', '1529, Borthwick Institute', True))
        elif text == "St Andrew's (from c.1220)":
            data.append(('St Andrew', 'from c.1220', True))
        elif text == 'St Andrew c. 1220':
            data.append(('St Andrew', 'c.1220', True))
        elif text == 'St Andrew c.1588':
            data.append(('St Andrew', 'c.1588', True))
        elif text == 'St Anne from 1538':
            data.append(('St Anne', 'from 1538', True))
        elif text == 'St Bartholomew until 1991':
            data.append(('St Bartholomew', 'until 1991', True))
        elif text == 'St Benedict and Holy Cross':
            data.append(('St Benedict', '', True))
            data.append(('Holy Cross', '', True))
        elif text == 'St Bilo (or St Milburg, abbess of Wenlock, 7thc.)':
            data.append(('St Bilo (or St Milburg, abbess of Wenlock, 7thc.)',
                         '', True))
        elif text == 'St Blathmac (?)':
            data.append(('St Blathmac', '', False))
        elif text == 'St Brecan (?)':
            data.append(('St Brecan', '', False))
        elif text == 'St Brigid (?)':
            data.append(('St Brigid', '', False))
        elif text == 'St George and All Saints':
            data.append(('St George', '', True))
            data.append(('All Saints', '', True))
        elif text == 'St Giles c.1120':
            data.append(('St Giles', 'c.1120', True))
        elif text == 'St Helen (1390, Prob. Reg.)':
            data.append(('St Helen', '1390, Prob. Reg.', True))
        elif text == 'St James 13thc.':
            data.append(('St James', '13thc.', True))
        elif text == 'St James c.1200':
            data.append(('St James', 'c.1200', True))
        elif text == 'St John c.1200, 1517':
            data.append(('St John', 'c.1200, 1517', True))
        elif text == 'St John in reign of Wm. Rufus; St John the Baptist in 1551':
            data.append(('St John', 'in reign of Wm. Rufus', True))
            data.append(('St John the Baptist', '1551', True))
        elif text == 'St John(reign of Wm. Rufus), St John the Baptist':
            data.append(('St John', 'reign of Wm. Rufus', True))
            data.append(('St John the Baptist', '', True))
        elif text == 'St John the Baptist (in 1551, Borthwick Institute)':
            data.append(('St John the Baptist', 'in 1551, Borthwick Institute',
                         True))
        elif text == 'St John the Baptist?':
            data.append(('St John the Baptist', '', False))
        elif text == 'St John the Baptist and St Alkmund':
            data.append(('St John the Baptist', '', True))
            data.append(('St Alkmund', '', True))
        elif text == 'St John the Evangelist (c.1150, SS James and John (c.1150), St John (1523)':
            data.append(('St John the Evangelist', 'c.1150', True))
            data.append(('St James', 'c.1150', True))
            data.append(('St John', 'c.1150', True))
            data.append(('St John', '1523', True))
        elif text == 'St Julian late 12thc.':
            data.append(('St Julian', 'late 12thc.', True))
        elif text == 'St Laurence (c.1190)':
            data.append(('St Laurence', 'c.1190', True))
        elif text == 'St Lawrence,':
            data.append(('St Lawrence', '', True))
        elif text == 'St Leonard 1341 (unconfirmed)':
            data.append(('St Leonard', '1341 (unconfirmed)', True))
        elif text == 'St Margaret (from)':
            data.append(('St Margaret', '', True))
        elif text == 'St Margaret 13thc.':
            data.append(('St Margaret', '13thc.', True))
        elif text == 'St Margaret1514':
            data.append(('St Margaret', '1514', True))
        elif text == 'St Margaret? 1520':
            data.append(('St Margaret', '1520', False))
        elif text == 'St Mary (1431, Prob. Reg.)':
            data.append(('St Mary', '1431, Prob. Reg.', True))
        elif text == 'St Mary, originally St Cwrda':
            data.append(('St Mary', '', True))
            data.append(('St Cwrda', 'originally', True))
        elif text == 'St Mary, latterly, St Margaret':
            data.append(('St Mary', '', True))
            data.append(('St Margaret', '', True))
        elif text == 'St Mary, St Benedict and Holy Cross':
            data.append(('St Mary', '', True))
            data.append(('St Benedict', '', True))
            data.append(('Holy Cross', '', True))
        elif text == 'St Mary?':
            data.append(('St Mary', '', False))
        elif text == 'St Mary1224':
            data.append(('St Mary', '1224', True))
        elif text == 'St Mary 13thc.':
            data.append(('St Mary', '13thc.', True))
        elif text == 'St Mary and All Saints':
            data.append(('St Mary', '', True))
            data.append(('All Saints', '', True))
        elif text == 'St Mary and All Saints 1763':
            data.append(('St Mary', '1763', True))
            data.append(('All Saints', '1763', True))
        elif text == 'St Mary and St Cuthbert 1187':
            data.append(('St Mary', '1187', True))
            data.append(('St Cuthbert', '1187', True))
        elif text == 'St Mary and St Thomas of Canterbury':
            data.append(('St Mary', '', True))
            data.append(('St Thomas of Canterbury', '', True))
        elif text == 'St Mary and the Holy Cross':
            data.append(('St Mary', '', True))
            data.append(('Holy Cross', '', True))
        elif text == 'St Mary before 1216':
            data.append(('St Mary', 'before 1216', True))
        elif text == 'St Mary Immaculate and St Joseph':
            data.append(('St Mary Immaculate', '', True))
            data.append(('St Joseph', '', True))
        elif text == 'St Mary Magdalene and St Denys 1764':
            data.append(('St Mary Magdalene', '1764', True))
            data.append(('St Denys', '1764', True))
        elif text == 'St Mary the Less (Little St Mary)':
            data.append(('St Mary the Less', '', True))
            data.append(('Little St Mary', '', True))
        elif text == 'St Mary the Virgin and All Saints':
            data.append(('St Mary the Virgin', '', True))
            data.append(('All Saints', '', True))
        elif text == 'St Mary the Virgin mid 12thc.':
            data.append(('St Mary the Virgin', 'mid 12thc.', True))
        elif text == 'St Mary with St John':
            data.append(('St Mary', '', True))
            data.append(('St John', '', True))
        elif text == 'St Mary (or St Andrew) 1086':
            data.append(('St Mary', '1086', True))
            data.append(('St Andrew', '1086', True))
        elif text == 'St Matthew1230':
            data.append(('St Matthew', '1230', True))
        elif text == 'St Michael and All Angels 18thc.':
            data.append(('St Michael and All Angels', '18thc.', True))
        elif text in ('St. Mchael and All Angels', 'St Michael & All Angels',
                      'St Michael and All Angels'):
            data.append(('St Michael', '', True))
            data.append(('All Angels', '', True))
        elif text == 'St Michael and All Saints':
            data.append(('St Michael', '', True))
            data.append(('All Saints', '', True))
        elif text == 'St Mogua (?)':
            data.append(('St Mogua', '', False))
        elif text == 'St Monacella/St Melangell':
            data.append(('St Monacella', '', True))
            data.append(('St Melangell', '', True))
        elif text == 'St Nicholas; St Thomas a Becket':
            data.append(('St Nicholas', '', True))
            data.append(('St Thomas a Becket', '', True))
        elif text == 'St Nicholas (before1099)':
            data.append(('St Nicholas', 'before 1099', True))
        elif text in ('St Nicholas and St Peter ad Vincula',
                      'St Nicholas (and St Peter ad Vincula)'):
            data.append(('St Nicholas', '', True))
            data.append(('St Peter ad Vincula', '', True))
        elif text == 'St Nicholas late 11thc.':
            data.append(('St Nicholas', 'late 11thc.', True))
        elif text == 'St Ninian, St Peter and St Paul':
            data.append(('St Ninian', '', True))
            data.append(('St Peter', '', True))
            data.append(('St Paul', '', True))
        elif text == 'St Patrick (?)':
            data.append(('St Patrick', '', False))
        elif text == 'St Peter?':
            data.append(('St Peter', '', False))
        elif text == 'St Peter 16thc.':
            data.append(('St Peter', '16thc.', True))
        elif text == 'St Peter and All Saints':
            data.append(('St Peter', '', True))
            data.append(('All Saints', '', True))
        elif text == 'St Peter and Paul':
            data.append(('St Peter', '', True))
            data.append(('St Paul', '', True))
        elif text == 'St Peter and St John the Baptist':
            data.append(('St Peter', '', True))
            data.append(('St John the Baptist', '', True))
        elif text == 'St Peter and St Paul 1556 and 1710':
            data.append(('St Peter', '1556 and 1710', True))
            data.append(('St Paul', '1556 and 1710', True))
        elif re.search(r'^St Peter and St Paul \(?(\d+)\)?$', text):
            match = re.search(r'^St Peter and St Paul \(?(\d+)\)?$', text)
            data.append(('St Peter', match.group(1), True))
            data.append(('St Paul', match.group(1), True))
        elif text == 'St Peter c.1200; 1408':
            data.append(('St Peter', 'c.1200; 1408', True))
        elif text == 'St Peter c.1300':
            data.append(('St Peter', 'c.1300', True))
        elif text == 'St Peter (1474), SS Peter & Paul (1510)':
            data.append(('St Peter', '1474', True))
            data.append(('St Peter', '1510', True))
            data.append(('St Paul', '1510', True))
        elif text == 'St Peter (1346, Prob. Reg.)':
            data.append(('St Peter', '1346, Prob. Reg.', True))
        elif text == 'St Saviour (1510-13), Holy Trinity (1513-17)':
            data.append(('St Saviour', '1510-13', True))
            data.append(('Holy Trinity', '1513-17', True))
        elif text == 'St Trunio and SS Peter and Paul':
            data.append(('St Trunio', '', True))
            data.append(('St Peter', '', True))
            data.append(('St Paul', '', True))
        elif text == '[? St Mary, originally St Cwrda]':
            data.append(('St Mary', '', False))
            data.append(('St Cwrda', 'originally', False))
        elif text == "The 'small church'":
            data.append(('The small church', '', True))
        elif text == 'unconfirmed':
            data.append(('not confirmed', '', True))
        else:
            for part in text.split(', '):
                pattern = r'^([^\d]*) \(?(\d+)\)?$'
                match = re.search(pattern, part)
                if match:
                    name = match.group(1)
                    date = match.group(2)
                else:
                    name = part
                    date = ''
                data.append((name, date, True))
        return data
