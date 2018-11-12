# These constants mirror (expected) values in the database. Changing
# them in one place and not the other will break expected behaviour.

DATE_NOW = 'now'
DATE_TRADITIONAL = 'pre-1974 traditional (England and Wales)'
DATE_TRADITIONAL_U = 'pre-1973 traditional (Ulster)'
DATE_TRADITIONAL_S = 'pre-1975 traditional (Scotland)'
DATE_TRADITIONAL_I = 'pre-1994 traditional (Republic of Ireland)'


DATE_HISTORIC = 'pre-1975'
DATE_MEDIEVAL = 'medieval'


REGION_TYPE_COUNTY = 'county'

SITE_STATUS_PUBLISHED = 'Accepted'
SITE_STATUS_PUBLISHED_INCOMPLETE = 'Accepted (incomplete)'
SITE_STATUS_DRAFT = 'Draft'
SITE_STATUS_DRAFT_IMO = 'Draft - images only'
SITE_STATUS_DRAFT_INC = 'Draft - incomplete'
SITE_STATUS_DRAFT_REP = 'Draft - report only'
SITE_STATUS_DRAFT_REV = 'Draft - revisit'
SITE_STATUS_NOROM = 'no romanesque sculpture'
SITE_STATUS_REVIEW = 'Ready for review'
SITE_STATUS_UNASSIGNED = 'Unassigned'
SITE_STATUS_UNREPORTED = 'Unreported'
FIELDWORKER_STATUSES = [SITE_STATUS_DRAFT, SITE_STATUS_DRAFT_IMO,
                        SITE_STATUS_DRAFT_INC, SITE_STATUS_DRAFT_REP,
                        SITE_STATUS_DRAFT_REV, SITE_STATUS_NOROM, SITE_STATUS_UNREPORTED]

FIELDWORKER_STATUSES_VISIBLE = [SITE_STATUS_DRAFT, SITE_STATUS_DRAFT_IMO,
                        SITE_STATUS_DRAFT_INC, SITE_STATUS_DRAFT_REP,
                        SITE_STATUS_DRAFT_REV, SITE_STATUS_NOROM,
                        SITE_STATUS_UNREPORTED,SITE_STATUS_REVIEW]



IMAGE_STATUS_GOOD = 'Good'
IMAGE_STATUS_POOR = 'Poor quality'
IMAGE_STATUS_SMALL = 'Too small'
IMAGE_STATUSES = [IMAGE_STATUS_GOOD, IMAGE_STATUS_POOR, IMAGE_STATUS_SMALL]

# Data on the British National Grid and Irish National Grid systems,
# which use lettered tiles as offsets for easting and northing values.

NG_TILES = {
    # BNG tiles
    'SV': [0,0], 'SW': [1,0], 'SX': [2,0], 'SY': [3,0], 'SZ': [4,0],
    'TV': [5,0], 'SQ': [0,1], 'SR': [1,1], 'SS': [2,1], 'ST': [3,1],
    'SU': [4,1], 'TQ': [5,1], 'TR': [6,1], 'SM': [1,2], 'SN': [2,2],
    'SO': [3,2], 'SP': [4,2], 'TL': [5,2], 'TM': [6,2], 'SG': [1,3],
    'SH': [2,3], 'SJ': [3,3], 'SK': [4,3], 'TF': [5,3], 'TG': [6,3],
    'SB': [1,4], 'SC': [2,4], 'SD': [3,4], 'SE': [4,4], 'TA': [5,4],
    'NW': [1,5], 'NX': [2,5], 'NY': [3,5], 'NZ': [4,5], 'OV': [5,5],
    'NQ': [0,6], 'NR': [1,6], 'NS': [2,6], 'NT': [3,6], 'NU': [4,6],
    'OQ': [5,6], 'NL': [0,7], 'NM': [1,7], 'NN': [2,7], 'NO': [3,7],
    'NP': [4,7], 'OL': [5,7], 'NF': [0,8], 'NG': [1,8], 'NH': [2,8],
    'NJ': [3,8], 'NK': [4,8], 'OF': [5,8], 'NA': [0,9], 'NB': [1,9],
    'NC': [2,9], 'ND': [3,9], 'NE': [4,9], 'OA': [5,9], 'HV': [0,10],
    'HW': [1,10], 'HX': [2,10], 'HY': [3,10], 'HZ': [4,10], 'JV': [5,10],
    'HQ': [0,11], 'HR': [1,11], 'HS': [2,11], 'HT': [3,11], 'HU': [4,11],
    'JQ': [5,11], 'HP': [4,12],
    # ING tiles
    'V': [0,0], 'W': [1,0], 'X': [2,0], 'Y': [3,0], 'Z': [4,0], 'Q': [0,1],
    'R': [1,1], 'S': [2,1], 'T': [3,1], 'U': [4,1], 'L': [0,2], 'M': [1,2],
    'N': [2,2], 'O': [3,2], 'P': [4,2], 'F': [0,3], 'G': [1,3], 'H': [2,3],
    'J': [3,3], 'K': [4,3], 'A': [0,4], 'B': [1,4], 'C': [2,4], 'D': [3,4],
    'E': [4,4]}

GRID_PATTERN = r'^(?P<bng>([HNST][A-HJ-Z]) (\d{2,5}) (\d{2,5}))$|^(?P<ing>([A-HJ-Z]) (\d{2,5}) (\d{2,5}))$'

MODEL_REFERENCE_PATTERN = r'\[(?P<model>[a-z_]+):(?P<id>\d+)\]'

ROTATE_JP2 = 'kdu_expand -i "%s" -rotate 90 -o "%s"'
CONVERT_TO_JP2 = 'kdu_compress -i "%s" -o "%s" -rate - Creversible=yes Clevels=5 Stiles="{1024,1024}" Cblk="{64,64}" Corder=RPCL'
