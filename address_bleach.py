from pathlib import Path
import textwrap


def compare(address1, address2):
    """ Compares the elements of two address_bleach.Address Objects.
        Returns list:
        MatchStatus: Match / No Match (str)-'No Match' will provide no score or additional match
                     criteria
        address1 Comparison Score: (float, 2 decimals)
        address2 Comparison Score: (float, 2 decimals)
        5-digit Zip Match: zip5_match (bool)
        City Match: city_match (bool)
        Directional Match: directional_match (bool)
    """

    def addr_body_compare(addr_breakdown_1, addr_breakdown_2):
        """ Compare elements between both addresses and return a match score. """
        elements = len(addr_breakdown_1)
        elmnt_mtch_ct = 0
        if elements == 0:
            return elements
        for k1, v1 in addr_breakdown_1.items():
            for k2, v2 in addr_breakdown_2.items():
                if v1 == v2:
                    elmnt_mtch_ct += 1
                    break
        elmnt_mtch_score = round(100 * elmnt_mtch_ct / elements, 0)
        return elmnt_mtch_score

    # Compare: Check if PO Box, if not, check if Street elements match.  Returns list:
    # [Match Value, Addr1_MatchScore, Addr2_MatchScore, Zip5_Match, City_Match,
    #  Directional_Match, Ste_Match]
    if address1.pobox_sts and address2.pobox_sts:
        if (address1.ca_box_number == address2.ca_box_number
            and address1.state == address2.state
        ):
            zip5_match = bool(address1.zipcode[:5] == address2.zipcode[:5])
            city_match = bool(address1.city.upper() == address2.city.upper())
            return ['Match', 100, 100, zip5_match, city_match, False, False]
    elif ((address1.pobox_sts and not address2.pobox_sts) or
          (not address1.pobox_sts and address2.pobox_sts)):
        return ['No Match', 0, 0, False, False, False, False]
    elif not address1.pobox_sts and not address2.pobox_sts:
        state_match = bool(address1.state == address2.state)
        if not state_match:
            return ['No Match', 0, 0, False, False, False, False]
        else:
            zip3_match = bool(address1.zipcode[:3] == address2.zipcode[:3])
            zip5_match = bool(address1.zipcode[:5] == address2.zipcode[:5])
            street_num_match = bool(address1.ca_street_num == address2.ca_street_num)
            block_match = bool(address1.ca_street_block == address2.ca_street_block)
            grid_match = bool(address1.ca_street_grid_id == address2.ca_street_grid_id)
            city_match = bool(address1.city.upper() == address2.city.upper())
            directional_match = bool(address1.ca_street_directional == address2.ca_street_directional)
            ste_match = bool(address1.ca_suite_num == address2.ca_suite_num)
            missing_ste = bool(not ste_match
                               and ((not address1.ca_suite_num and address2.ca_suite_num)
                                    or (address1.ca_suite_num and not address2.ca_suite_num)))
            zip3_plus_streetnum_chks = bool(zip3_match
                                            and street_num_match
                                            and block_match
                                            and grid_match)
            ste_chk = bool((not ste_match and missing_ste) or ste_match)
            if zip3_plus_streetnum_chks and ste_chk:
                addr1_body_score = \
                    addr_body_compare(address1.address_breakdown, address2.address_breakdown)
                addr2_body_score = \
                    addr_body_compare(address2.address_breakdown, address1.address_breakdown)

                if addr1_body_score == 0 or addr2_body_score == 0:
                    return ['No Match', addr1_body_score, addr2_body_score,
                            zip5_match, city_match, directional_match, ste_match]
                else:
                    if zip5_match or city_match:
                        return ['Match', addr1_body_score, addr2_body_score,
                                zip5_match, city_match, directional_match, ste_match]
                    elif addr1_body_score == 100.0 and addr2_body_score == 100.0:
                        return ['Match', addr1_body_score, addr2_body_score,
                                zip5_match, city_match, directional_match, ste_match]
                    return ['Potential', addr1_body_score, addr2_body_score,
                            zip5_match, city_match, directional_match, ste_match]
    return ['No Match', 0, 0, False, False, False, False]


class Address:
    """ Address Object for address_bleach, which is intended to make
        the cleanup and comparison of address data much easier by
        breaking the data down into more manageable components. """

    def __init__(self, address, city, state, zipcode, wdir=str(Path.cwd())):

        self.address = address
        self.city = city
        self.state = state
        self.zipcode = zipcode
        self.pobox_sts = False
        self.block_sts = False
        self.address_details = \
            {'grid': '', 'street_block': '', 'street_num': '', 'street_body': '',
             'street_suffix': '', 'street_directional': '', 'suite_num': '', 'box_num': ''}
        # self.ca_street_grid_id = ''
        # self.ca_street_block = ''
        # self.ca_street_num = ''
        # self.ca_street_body = ''
        # self.ca_street_suffix = ''
        # self.ca_street_directional = ''
        # self.ca_suite_num = ''
        # self.ca_box_number = ''
        self.address_breakdown = {}
        self.exceptions = []
        self.exception_cases_file = wdir + '\\AddressBleach_LoggedExceptions.csv'

        # Perform evaluation and breakdown
        self.pobox_sts, self.address_details['box_num'] = self.is_pobox()

    def __str__(self):
        details = f'''\
                      Raw Address: {self.address}
                      Raw City: {self.city}
                      Raw State: {self.state}
                      Raw Zip: {self.zipcode}
                      Po Box?: {self.pobox_sts}
                      Block Address?: {self.block_sts}
                      Grid ID: {self.address_details['grid']}
                      Street Block: {self.address_details['street_block']}
                      Street Number: {self.address_details['street_num']}
                      Street Body: {self.address_details['street_body']}
                      Street Suffix: {self.address_details['street_suffix']}
                      Street Directional: {self.address_details['street_directional']}
                      Street Suite Number: {self.address_details['suite_num']}
                      PO Box Number: {self.address_details['box_num']}'''
        return textwrap.dedent(details)

    def is_pobox(self):
        """ Identifies whether address is a PO Box.  Returns boolean. """
        box_num = ''
        r_val = False
        if len(self.address.split(' ')) == 1:
            r_val = False
        else:
            po_segment_zero = self.address.split(' ')[0]
            po_segment_one = self.address.split(' ')[1]
            frst_space = str(self.address).find(' ')
            scnd_space = str(self.address).find(' ', frst_space + 1)
            thrd_space = str(self.address).find(' ', scnd_space + 1)
            if (po_segment_zero.upper() == 'PO'
                    and po_segment_one.upper() == 'BOX'):
                box_num_scnd = ''.join([s for s in str(self.address)[scnd_space:]])
                box_num = box_num_scnd
                r_val = True
            elif (po_segment_zero.upper() == 'P'
                  and po_segment_one.upper() == 'O'):
                box_num_thrd = ''.join([s for s in str(self.address)[thrd_space:]])
                box_num = box_num_thrd
                r_val = True
        return r_val, box_num

    def breakdown_details(self):
        """ Separates the address into workable/comparable pieces. """

        def is_grid_element(index, element):
            """ Identifies Grid numbers.  Returns boolean. """
            return bool((int(index) == 0 and
                         '-' not in element and
                         len([c for c in element if c.isalpha()]) == 2))

        def is_block_address(index, element):
            """ Identifies Block Address.  Returns boolean. """
            return bool((int(index) in [0, 1] and
                         '-' in element and
                         len([c for c in element if c.isalpha()]) == 0 and
                         len(element.split('-')[1]) > 2))

        def is_directional(element):
            """ Identifies if element is a directional.  Returns boolean. """
            return bool(element.upper() in ['N', 'S', 'E', 'W', 'NW', 'NE', 'SW', 'SE', 'NORTH', 'SOUTH',
                                            'EAST', 'WEST', 'NORTHWEST', 'NORTHEAST', 'SOUTHWEST',
                                            'SOUTHEAST'])

        def is_streetnum(index, element):
            """ Idenfies street number.  Returns boolean. """
            # TODO: Check for a int
            if (not self.block_sts and
                    not self.ca_street_grid_id and
                    int(index) == 0
            ):
                return True
            elif self.block_sts:
                return False
            elif ((not self.block_sts and
                   self.ca_street_grid_id) and
                  int(index) == 1):
                return True
            elif (self.block_sts and
                  self.ca_street_grid_id and
                  int(index) == 2):
                return False
            return False

        def street_number(element):
            """ Identifies Street Number and, if applicable, the Suite Suffix.
                Returns Street Number as String and Suite Suffix as String or '' """
            ste_suffix = ''
            nums = ''.join([c for c in element.split('-')[0] if c.isdigit()])
            # Check for Ste Suffix #
            if element.isalnum():
                # '123B' Main Street
                ste_suffix = ''.join([c for c in element if c.isalpha()])
            elif '-' in element:
                # '123-A' Main Street
                # '123-4' Main Street
                ste_suffix = element.split('-')[1]
            else:
                pass
            return nums, ste_suffix

        def has_suite(address):
            """ Identifies if address has suite.  Returns boolean. """
            found_ste = False
            found_value = ''
            ste_ids = [' BLDG ', ' FLOOR ', ' FL ', ' FLR ', ' APT ', ' UNIT ', '#', ' ROOM ',
                       'SPC', 'FRNT', ' RM ', ' SUITE ', ' STE ', ' #', ' # ']
            for identifier in ste_ids:
                if identifier in address.upper():
                    found_ste = True
                    found_value = identifier
            return found_ste, found_value

        def ste_number(address, ste_value):
            ste_len = len(ste_value)
            index_ste = address.upper().find(ste_value)
            exclude_ste_val = index_ste + ste_len  # Updates index number to exclude 'Ste' or 'Room'
            first_pass = ''.join([str(s) for s in str(address)[exclude_ste_val:]])
            fp_space_index = str(first_pass).find(' ')
            if fp_space_index != -1:
                # Check that this piece is working properly #
                ste_number = \
                    ''.join([str(i) for i in str(first_pass).replace('-', '')[:fp_space_index]])
            else:
                ste_number = str(first_pass).replace('-', '')

            return ste_number

        def identify_directional(potentials):
            """ Identify Directional based on last directional received in an address
            Example: 123 N Carolina St SE
            We would not want to consider 'N' in this address to be the directional
            Considered situation (see absolute difference line: 123 SE N Carolina
            {1:'N', 4:'NW'} """
            # TODO: (May need to change positioning of Suite Identifier)
            potential_keys = [int(k) for k in potentials.keys()]
            directional_val = ''
            directional_key = ''
            if len(potentials) == 2:
                if abs(potential_keys[1] - potential_keys[0]) > 1:
                    directional_val = potentials[str(max(potential_keys))]
                    directional_key = max(potential_keys)
                else:
                    directional_val = potentials[str(min(potential_keys))]
                    directional_key = min(potential_keys)
            elif len(potentials) == 1:
                directional_val = potentials[str(min(potential_keys))]
                directional_key = min(potential_keys)
            else:
                # More than 2 directionals observed...document it and figure out why it exists
                # In case it's not evident, this shouldn't occur
                self.exceptions.append({'Address': self.address, 'City': self.city,
                                        'State': self.state, 'Zip': self.zipcode,
                                        'Exception': 'More than 2 potential Directionals exist in address.'})
            return directional_val, str(directional_key)

        def identify_street_suffix(address_bd):
            street_abbreviations = {'ALY': 'ALY', 'ALLEY': 'ALY', 'AVE': 'AVE', 'AVENUE': 'AVE',
                                    'BYU': 'BYU', 'BAYOU': 'BYU', 'BCH': 'BCH', 'BEACH': 'BCH', 'BND': 'BND',
                                    'BEND': 'BND', 'BLF': 'BLF', 'BLUFF': 'BLF', 'BLVD': 'BLVD', 'BOULEVARD': 'BLVD',
                                    'BRG': 'BRG', 'BRIDGE': 'BRG', 'BRDGE': 'BRG', 'BYP': 'BYP', 'BYPASS': 'BYP',
                                    'BYPA': 'BYP', 'BYPS': 'BYP', 'CSWY': 'CSWY', 'CAUSEWAY': 'CSWY', 'CIR': 'CIR',
                                    'CIRCLE': 'CIR', 'CRCL': 'CIR', 'COURT': 'CT', 'CT': 'CT', 'DR': 'DR', 'DRIV': 'DR',
                                    'DRIVE': 'DR', 'DRV': 'DR', 'EXPRESSWAY': 'EXPY', 'EXPY': 'EXPY', 'EXPW': 'EXPY',
                                    'FREEWAY': 'FWY', 'FRWY': 'FWY', 'FWY': 'FWY', 'GATEWAY': 'GTWY', 'GTWY': 'GTWY',
                                    'GTWAY': 'GTWY', 'HIGHWAY': 'HWY', 'HWAY': 'HWY', 'HWY': 'HWY', 'JCT': 'JCT',
                                    'JCTION': 'JCT', 'JUNCTION': 'JCT', 'JUNCTN': 'JCT', 'JCTN': 'JCT', 'LOOP': 'LOOP',
                                    'LOOPS': 'LOOP', 'LN': 'LN', 'LANE': 'LANE', 'MOTORWAY': 'MTWY', 'MTWY': 'MTWY',
                                    'PARKWAY': 'PKWY', 'PKWY': 'PKWY', 'PKWAY': 'PKWY', 'PKY': 'PKWY', 'PARKWY': 'PKWY',
                                    'RD': 'RD', 'ROAD': 'ROAD', 'ROUTE': 'RTE', 'RTE': 'RTE', 'SQ': 'SQ',
                                    'SQUARE': 'SQ',
                                    'SQR': 'SQ', 'SQRE': 'SQ', 'STREET': 'ST', 'STRT': 'ST', 'ST': 'ST', 'STR': 'ST',
                                    'TRAIL': 'TRL', 'TRL': 'TRL', 'TRNPK': 'TPKE', 'TURNPIKE': 'TPKE', 'TURNPK': 'TPKE',
                                    'TPKE': 'TPKE', 'WAY': 'WAY', 'WY': 'WAY'}
            found_suffix = ''
            suffix_key = ''
            for element_key, element_value in address_bd:
                for suffix_value, suffix_abbreviation in street_abbreviations.items():
                    if element_value.upper() == suffix_value:
                        found_suffix = suffix_abbreviation
                        suffix_key = element_key
                        break

            return found_suffix, suffix_key

        def remove_found_types(r_list):
            """ Remove identified address pieces. """
            for key in r_list:
                if key:
                    try:
                        self.address_breakdown.pop(key)
                    except KeyError as key_err:
                        print(f'Address_Bleach: Key Error encountered: {self.address} \
{self.address_breakdown}, {key_err}, {r_list}')
            r_list.clear()

        # Begin Address Breakdown #
        if self.is_pobox():
            pass
        else:
            removals = set()
            # [Grid][StreetNum][StreetNumSuffixOrDirectional][StreetBody]
            # [StreetBodyDirectional][SteBldg Extension]
            # Build breakdown dictionary #
            for n, element in enumerate(self.address.split(' ')):
                self.address_breakdown[str(n)] = element
            # Check for Suite Numbers #
            body_ste_chk, body_ste_id = has_suite(self.address)
            if body_ste_chk:
                self.ca_suite_num = ste_number(self.address, body_ste_id)
                for k, v in self.address_breakdown.items():
                    if v.upper() == body_ste_id.strip():
                        removals.add(k)
                    elif v == self.ca_suite_num:
                        removals.add(k)
                    elif body_ste_id.strip() in v:
                        removals.add(k)
                    else:
                        pass
            else:
                pass
            # Removal of elements identified from breakdown dictionary.
            # Occurs throughout identification process.
            remove_found_types(removals)
            potential_directionals = {}

            # Identification of Grid and Block address elements.
            for k, v in self.address_breakdown.items():
                if is_grid_element(k, v):
                    self.ca_street_grid_id = v
                    removals.add(k)
                elif is_block_address(k, v):
                    self.block_sts = True
                    self.ca_street_block = v
                    removals.add(k)
            remove_found_types(removals)

            # Identification of Street Number and, if applicable, Ste Number
            for k, v in self.address_breakdown.items():
                if is_streetnum(k, v):
                    self.ca_street_num, potential_ste = street_number(v)
                    if not self.ca_suite_num:
                        self.ca_suite_num = potential_ste
                    removals.add(k)

            self.ca_street_suffix, suff_key = identify_street_suffix(self.address_breakdown.items())
            removals.add(suff_key)
            remove_found_types(removals)

            # Identification of Directional
            for k, v in self.address_breakdown.items():
                if is_directional(v):
                    potential_directionals[k] = v

            self.ca_street_directional, match_key = identify_directional(potential_directionals)
            if match_key:
                removals.add(match_key)
                remove_found_types(removals)

            self.ca_street_body = ' '.join(self.address_breakdown.values())
