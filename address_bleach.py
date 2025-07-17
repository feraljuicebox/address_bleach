from pathlib import Path
from csv import DictReader
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
        breaking the data down into more manageable components."""

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
        # Files/Exceptions
        self.files = {'suite_identifiers':
                      str(Path(__file__).parent.absolute()) + '\\address_bleach\\ste_identifiers',
                      'exception': wdir + '\\AddressBleach_LoggedExceptions.csv'}
        self.exceptions = []
        # Perform evaluation and breakdown
        self.pobox_sts, self.address_details['box_num'] = self.is_pobox()
        if not self.pobox_sts:
            self.address_breakdown = self.address_breakdown(dict())

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

    def breakdown_details(self, bd_dict):
        """ Separates the address into workable/comparable pieces.
        Breakdown occurs to identify the following pieces:
        [Grid][StreetNum]
        [StreetNumSuffixOrDirectional]
        [StreetBody]
        [StreetBodyDirectional]
        [SteBldg Extension]
        Returns dict()."""
        def remove_found_types(r_list, breakdown_detail_dict):
            """ Remove identified address pieces. Returns empty set"""
            for key in r_list:
                if key:
                    try:
                        breakdown_detail_dict.pop(key)
                    except KeyError as key_err:
                        print(f'Address_Bleach: Key Error encountered: {self.address}'
                              + f'{self.address_breakdown}, {key_err}, {r_list}')
            return set(), breakdown_detail_dict

        def find_suite(full_address, suite_identifiers):
            """ Identifies if address has suite.  Returns boolean. """
            found_ste = False
            found_value = ''
            ste_number = ''
            # Load Suite Identifiers
            with open(suite_identifiers, 'r') as si_in:
                si_rdr = DictReader(si_in)
                ste_ids = [x['Identifier'] for x in si_rdr]
            for identifier in ste_ids:
                if identifier in full_address.upper():
                    found_ste = True
                    found_value = identifier
            if found_ste:
                # Now that we have found it, let's get it!
                id_len = len(found_value)
                index_ste = full_address.upper().find(found_value)
                exclude_ste_val = index_ste + id_len
                isolated_suite = str(full_address)[exclude_ste_val:]
                iso_ste_index = str(isolated_suite).find(' ')
                if iso_ste_index != -1:
                    # If there is a space found after the identifier, only pull what is prior to.
                    ste_number = str(isolated_suite).replace('-', '')[:iso_ste_index]
                else:
                    ste_number = str(isolated_suite).replace('-', '')
            return found_ste, found_value, ste_number

        def is_grid_element(index, element):
            """ Identifies Grid numbers by looking at the first indexed element of the breakdown
            details dict.  If a dash isn't found in this element, and the length of the element
            where the value is alpha  Returns boolean.
            Examples:
            N6W23001 BLUEMOUND RD
            39.2 RD
            """
            return bool(all([index == 0,
                             any(['-' not in element
                                  and len([c for c in element if c.isalpha()]) == 2,
                                  '.' in element])]))

        def is_block_address(index, element):
            """ Identifies Block Address.  Returns boolean.
            Example:
            112-10 BRONX RD
            """
            return bool(all([index in [0, 1], '-' in element,
                             len([c for c in element if c.isalpha()]) == 0,
                             len(element.split('-')[1]) > 2]))

        def find_street_num(index, element, block_ind, grid_ck):
            """ Idenfies street number.  Returns boolean.
            Identifies Street Number and, if applicable, the Suite Suffix.
            Returns Street Number as String and Suite Suffix as String or '' """
            def word_conversion(word):
                '''For those -fancy- type people who can't bother to use a normal street number.
                Mind you, this expects a single element that uses a word instead of a number, so
                your mileage may vary.'''
                words = {'ONE': '1', 'TWO': '2', 'THREE': '2', 'FOUR': '4', 'FIVE': '5', 'SIX': '6',
                         'SEVEN': '7', 'EIGHT': '8', 'NINE': '9', 'TEN': '10', 'ELEVEN': '11',
                         'TWELVE': '12', 'THIRTEEN': '13', 'FOURTEEN': '14', 'FIFTEEN': '15',
                         'SIXTEEN': '16', 'SEVENTEEN': '17', 'EIGHTEEN': '18', 'NINETEEN': '19',
                         'TWENTY': '20', 'THIRTY': '30', 'FORTY': '40', 'FIFTY': '50',
                         'SIXTY': '60', 'SEVENTY': '70', 'EIGHTY': '80', 'NINETY': '90'}
                converted_word = False
                if word.upper() in words.keys():
                    converted_word = words[word.upper()]
                return converted_word

            if index <= 1 and element.isalpha():
                element_conv = word_conversion(element)
            true_conditionals = all([any([all([not block_ind, not grid_ck, index == 0]),
                                          all([not block_ind, grid_ck, index == 1])]),
                                     len([c for c in element if c.isdigit()]) == len(element)])
            ste_suffix = ''
            nums = ''
            if true_conditionals:
                nums = ''.join([c for c in element.split('-')[0] if c.isdigit()])
                if not nums and element_conv:
                    nums = element_conv
                # Check for Ste Suffix #
                if element.isalnum() and len([c for c in element if c.isalnum()]) != len(element):
                    # '123B' Main Street
                    ste_suffix = ''.join([c for c in element if c.isalpha()])
                elif '-' in element:
                    # '123-A' Main Street
                    # '123-4' Main Street
                    ste_suffix = element.split('-')[1]

            return nums, ste_suffix

        def identify_street_suffix(address_bd, suffix_identifiers):
            '''Loops through the remaining items in Address Breakdown in reverse order searching for
            a valid suffix.  Those items are then checked against the values listed in
            suffix_identifiers.csv which is populated with translations provided by the USPS.
            Given that suffixes are at the end of the address, we're reversing the dict() order to
            get there faster and not accidentally capture a part of the street body by mistake
            first, such as with PEACEFUL TRAIL RD picking up TRAIL first.'''
            with open(suffix_identifiers, 'r') as sfx_in:
                sfx_rdr = DictReader(sfx_in)
                sfx_ids = {x['Value']: x['Conversion'] for x in sfx_rdr}
            found_suffix = ''
            suffix_key = ''
            reverse_index_bd = dict(reversed(address_bd.items()))
            for element_key, element_value in reverse_index_bd:
                for suffix_value, suffix_abbreviation in sfx_ids.items():
                    if element_value.upper() == suffix_value:
                        found_suffix = suffix_abbreviation
                        suffix_key = element_key
                        break

            return found_suffix, suffix_key

        def find_directional(address_bd):
            '''Identify Directional based on last directional received in an address
            Example: 123 N Carolina St SE
            We would not want to consider 'N' in this address to be the directional
            Considered situation (see absolute difference line: 123 SE N Carolina
            Directional: SE
            Example: 456 South Edgar St West
            That said, you could have a situation where the directional is actually the first
            observed directional; in this case it is "S".  This process will not identify it this
            way.
            Directional: W
            Example: 789 N West Side Rd
            Even more confusingly, you could get a directional prior to another word that could be
            considered a directional.  Obviously, in this case, the desire is to identify 'N' as the
            directional in this case.
            NOTE: I have not been able to find any documentation to determine a hierarchy, so, until
            that surfaces, I will just have to make some assumptions about which directional is the
            valid directional.  Realistically, this shouldn't impact matching, as both similar
            addresses should present their directional the same, but it's still worth noting.
            '''
            potentials = dict()
            exceptions = []
            for k, v in address_bd.items():
                if v.upper() in ['N', 'S', 'E', 'W', 'NW', 'NE', 'SW', 'SE', 'NORTH', 'SOUTH',
                                 'EAST', 'WEST', 'NORTHWEST', 'NORTHEAST', 'SOUTHWEST',
                                 'SOUTHEAST']:
                    potentials[k] = v
            potential_keys = [k for k in potentials.keys()]
            directional_key = None
            directional_val = ''
            if potential_keys == 2:
                if abs(potential_keys[1] - potential_keys[0]) > 1:
                    # Position of each directional is greater than one element away from each other.
                    # 123 N Carolina St SE - Grabs SE
                    directional_key = max(potential_keys)
                    directional_val = potentials[max(potential_keys)]
                else:
                    # Position of each directional is next to each other.
                    # 789 N West Side Rd - Grabs N
                    directional_key = min(potential_keys)
                    directional_val = potentials[min(potential_keys)]
            elif len(potentials) == 1:
                directional_key = min(potential_keys)
                directional_val = potentials[min(potential_keys)]
            else:
                # More than 2 directionals observed...document it and figure out why it exists
                # In case it's not evident, this shouldn't occur
                exceptions\
                    .append({'Address': self.address, 'City': self.city,
                             'State': self.state, 'Zip': self.zipcode,
                             'Exception': 'More than 2 potential Directionals exist in address.'})
            return directional_val, directional_key, exceptions

        # Begin Address Breakdown #
        removals = set()
        # Build breakdown dictionary #
        for n, element in enumerate(self.address.split(' ')):
            bd_dict[n] = element
        # Check for Suite Numbers #
        body_ste_chk, body_ste_id, addr_ste_num = \
            find_suite(self.address, self.files['ste_identifiers'])
        if body_ste_chk:
            # Assign breakdown removals
            for k, v in bd_dict.items():
                conditionals = any([v.upper() == body_ste_id.strip(),
                                    v == addr_ste_num,
                                    body_ste_id.strip() in v])
                if conditionals:
                    removals.add(k)
                else:
                    pass
        else:
            pass
        removals, bd_dict = remove_found_types(removals)

        # Identification of Grid and Block address elements.
        for k, v in bd_dict.items():
            if is_grid_element(k, v):
                grid_id = v
                removals.add(k)
            elif is_block_address(k, v):
                block_status = True
                street_block = v
                removals.add(k)
        removals, bd_dict = remove_found_types(removals)

        # Identification of Street Number and, if applicable, Ste Number
        for k, v in bd_dict.items():
            street_number, potential_ste = find_street_num(k, v, block_status, bool(grid_id))
            if not addr_ste_num:
                addr_ste_num = potential_ste
            removals.add(k)

        street_suffix, suff_key = identify_street_suffix(bd_dict)
        removals.add(suff_key)
        removals, bd_dict = remove_found_types(removals)

        # Identification of Directional
        street_directional, match_key, dir_exceptions = find_directional(bd_dict)
        if dir_exceptions:
            # TODO: Manage Exceptions
            pass
        if match_key:
            removals.add(match_key)
            remove_found_types(removals)

        # Compile Body
        street_body = ' '.join(bd_dict.values())

        return addr_ste_num, grid_id, block_status, street_block, street_number, street_suffix, \
            street_directional, street_body
