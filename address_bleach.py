from pathlib import Path
from csv import DictReader
import textwrap


def compare(address1, address2):
    """ Compares the elements of two address_bleach.Address Objects.
        Returns dict:
        Match_Status: Match / No Match / Potential (str)
                      NOTE: 'No Match' will provide no score or additional match criteria.
        Address1_Body_Score: (float, 2 decimals)
        Address2_Body_Score: (float, 2 decimals)
        Zip5_Match: zip5_match (bool)
        City_Match: city_match (bool)
        Directional_Match: directional_match (bool)
        Ste_Match: ste_match (bool)
        [Match_Status, Address1_Body_Score, Address2_Body_Score, Zip5_Match, City_Match,
         Directional_Match, Ste_Match]
         TODO: Add functionality to ignore suite number in comparison findings if desired.
    """

    def addr_body_compare(addr_breakdown_1, addr_breakdown_2):
        """ Compare elements between both addresses and return a match score. """
        addr_breakdown_1 = addr_breakdown_1.split(' ')
        addr_breakdown_2 = addr_breakdown_2.split(' ')
        elements = len(addr_breakdown_1)
        elmnt_mtch_score = 0
        elmnt_mtch_ct = 0
        if elements > 0:
            for v1 in addr_breakdown_1:
                for v2 in addr_breakdown_2:
                    if v1 == v2:
                        elmnt_mtch_ct += 1
                        break
            elmnt_mtch_score = round(100 * elmnt_mtch_ct / elements, 0)
        return elmnt_mtch_score

    comparison_decision = {'Match_Status': 'No Match', 'Address1_Body_Score': 0,
                           'Address2_Body_Score': 0, 'Zip5_Match': False, 'City_Match': False,
                           'Directional_Match': False, 'Ste_Match': False}
    zip3_match = bool(address1.zipcode[:3] == address2.zipcode[:3])
    zip5_match = bool(address1.zipcode[:5] == address2.zipcode[:5])
    city_match = bool(address1.city.upper() == address2.city.upper())
    # Compare: Check if PO Box, if not, check if Street elements match.
    if address1.pobox_sts and address2.pobox_sts:
        if (address1.address_details['box_num'] == address2.address_details['box_num']
                and address1.state.upper() == address2.state.upper()):
            comparison_decision = {'Match_Status': 'Match', 'Address1_Body_Score': 100,
                                   'Address2_Body_Score': 100, 'Zip5_Match': zip5_match,
                                   'City_Match': city_match, 'Directional_Match': False,
                                   'Ste_Match': False}
    elif ((address1.pobox_sts and not address2.pobox_sts)
          or (not address1.pobox_sts and address2.pobox_sts)):
        comparison_decision = {'Match_Status': 'No Match', 'Address1_Body_Score': 0,
                               'Address2_Body_Score': 0, 'Zip5_Match': False, 'City_Match': False,
                               'Directional_Match': False, 'Ste_Match': False}
    elif not address1.pobox_sts and not address2.pobox_sts:
        state_match = bool(address1.state.upper() == address2.state.upper())
        if not state_match:
            comparison_decision = {'Match_Status': 'No Match', 'Address1_Body_Score': 0,
                                   'Address2_Body_Score': 0, 'Zip5_Match': False,
                                   'City_Match': False, 'Directional_Match': False,
                                   'Ste_Match': False}
        else:
            street_num_match = bool(address1.address_details['street_num']
                                    == address2.address_details['street_num'])
            block_match = bool(address1.address_details['street_block']
                               == address2.address_details['street_block'])
            grid_match = bool(address1.address_details['grid'] == address2.address_details['grid'])
            directional_match = \
                bool(address1.address_details['street_directional']
                     == address2.address_details['street_directional'])
            ste_match = bool(address1.address_details['suite_num']
                             == address2.address_details['suite_num'])
            missing_ste = all([not ste_match,
                               any([not address1.address_details['suite_num'],
                                    not address2.address_details['suite_num']])])
            zip3_plus_streetnum_chks = all([zip3_match, street_num_match, block_match, grid_match])
            ste_chk = any([not ste_match and missing_ste, ste_match])
            if zip3_plus_streetnum_chks and ste_chk:
                # Confirmed 3-digit Zip, street numbers, and block/grid match
                # Suite numbers either match or one is populated and the other is not.
                addr1_body_score = \
                    addr_body_compare(address1.address_details['street_body'],
                                      address2.address_details['street_body'])
                addr2_body_score = \
                    addr_body_compare(address2.address_details['street_body'],
                                      address1.address_details['street_body'])

                if addr1_body_score == 0 or addr2_body_score == 0:
                    # Completely different Street Bodies
                    comparison_decision = \
                        {'Match_Status': 'No Match', 'Address1_Body_Score': addr1_body_score,
                         'Address2_Body_Score': addr2_body_score, 'Zip5_Match': zip5_match,
                         'City_Match': city_match, 'Directional_Match': directional_match,
                         'Ste_Match': ste_match}
                elif ((zip5_match or city_match)
                      or (addr1_body_score == 100.0 and addr2_body_score == 100.0)):
                    comparison_decision = \
                        {'Match_Status': 'Match', 'Address1_Body_Score': addr1_body_score,
                            'Address2_Body_Score': addr2_body_score,
                            'Zip5_Match': zip5_match, 'City_Match': city_match,
                            'Directional_Match': directional_match, 'Ste_Match': ste_match}
                else:
                    comparison_decision = \
                        {'Match_Status': 'Potential', 'Address1_Body_Score': addr1_body_score,
                         'Address2_Body_Score': addr2_body_score, 'Zip5_Match': zip5_match,
                         'City_Match': city_match, 'Directional_Match': directional_match,
                         'Ste_Match': ste_match}
    return comparison_decision


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
        self.address_details = \
            {'grid': '', 'street_block': '', 'street_num': '', 'street_body': '',
             'street_suffix': '', 'street_directional': '', 'suite_num': '', 'box_num': ''}
        # Files/Exceptions
        self.files = {'ste_identifiers': str(Path(__file__).parent.absolute())
                      + '\\address_bleach\\ste_identifiers.csv',
                      'sfx_identifiers': str(Path(__file__).parent.absolute())
                      + '\\address_bleach\\suffix_identifiers.csv',
                      'exception': wdir + '\\AddressBleach_LoggedExceptions.csv'}
        self.exceptions = []
        # Perform evaluation and breakdown
        self.pobox_sts, self.address_details['box_num'] = self.is_pobox()
        if not self.pobox_sts:
            self.address_details, self.exceptions = \
                self.breakdown_details(dict(), self.address_details['box_num'])

    def __str__(self):
        details = f'''\
                      Raw Address: {self.address}
                      Raw City: {self.city}
                      Raw State: {self.state}
                      Raw Zip: {self.zipcode}
                      Po Box?: {self.pobox_sts}
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

    def breakdown_details(self, bd_dict, box_num):
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
                if str(key):
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
            block_check = False
            if len(element.split('-')) > 1:
                block_check = all([index in [0, 1], '-' in element,
                                   len([c for c in element if c.isalpha()]) == 0,
                                   len(element.split('-')[1]) >= 2])
            return block_check

        def find_street_num(address_bd, block_ind, grid_ck):
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

            ste_suffix = ''
            temp_val = ''
            nums = ''
            found_key = ''
            for k, v in address_bd.items():
                true_conditionals = all([any([all([not block_ind, not grid_ck, k == 0]),
                                              all([not block_ind, grid_ck, k == 1])]),
                                         len([c for c in v if c.isdigit()]) >= 1])
                if true_conditionals and not v.isalpha():
                    nums = ''.join([c for c in v.split('-')[0] if c.isdigit()])
                    temp_val = v
                elif true_conditionals and k <= 1 and v.isalpha():
                    nums = word_conversion(v)
                if nums:
                    found_key = k
                    break
            # Check for Ste Suffix #
            if temp_val:
                if (temp_val.isalnum()
                        and len([c for c in temp_val if c.isalpha()]) != len(temp_val)):
                    # '123B' Main Street
                    ste_suffix = ''.join([c for c in v if c.isalpha()])
                elif '-' in v:
                    # '123-A' Main Street
                    # '123-4' Main Street
                    ste_suffix = v.split('-')[1]

            return nums, ste_suffix, found_key

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
            for element_key, element_value in reverse_index_bd.items():
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
            conversion = {'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W', 'NORTHWEST': 'NW',
                          'NORTHEAST': 'NE', 'SOUTHWEST': 'SW', 'SOUTHEAST': 'SE'}
            for k, v in address_bd.items():
                if v.upper() in ['N', 'S', 'E', 'W', 'NW', 'NE', 'SW', 'SE', 'NORTH', 'SOUTH',
                                 'EAST', 'WEST', 'NORTHWEST', 'NORTHEAST', 'SOUTHWEST',
                                 'SOUTHEAST']:
                    potentials[k] = v
            potential_keys = [k for k in potentials.keys()]
            directional_key = None
            directional_val = ''
            if len(potential_keys) == 2:
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
            if directional_val.upper() in conversion.keys():
                directional_val = conversion[directional_val.upper()]
            return directional_val, directional_key, exceptions

        # Begin Address Breakdown #
        removals = set()
        bd_exceptions = []
        # Build breakdown dictionary #
        for n, element in enumerate(self.address.split(' ')):
            bd_dict[n] = element
        # Check for Suite Numbers #
        body_ste_chk, body_ste_id, addr_ste_num = \
            find_suite(self.address, self.files['ste_identifiers'])
        if body_ste_chk:
            # Assign breakdown removals
            for ste_k, ste_v in bd_dict.items():
                conditionals = any([ste_v.upper() == body_ste_id.strip(),
                                    ste_v == addr_ste_num,
                                    body_ste_id.strip() in ste_v])
                if conditionals:
                    removals.add(ste_k)
                else:
                    pass
        else:
            pass
        removals, bd_dict = remove_found_types(removals, bd_dict)

        # Identification of Grid and Block address elements.
        block_status = False
        grid_id = ''
        street_block = ''
        for gb_k, gb_v in bd_dict.items():
            if is_grid_element(gb_k, gb_v):
                grid_id = gb_v
                removals.add(gb_k)
            elif is_block_address(gb_k, gb_v):
                block_status = True
                street_block = gb_v
                removals.add(gb_k)
        removals, bd_dict = remove_found_types(removals, bd_dict)

        # Identification of Street Number and, if applicable, Ste Number
        street_number, potential_ste, key = find_street_num(bd_dict, block_status, bool(grid_id))
        if street_number:
            removals.add(key)
        if not addr_ste_num and potential_ste:
            addr_ste_num = potential_ste
        removals, bd_dict = remove_found_types(removals, bd_dict)

        street_suffix, suff_key = identify_street_suffix(bd_dict, self.files['sfx_identifiers'])
        removals.add(suff_key)
        removals, bd_dict = remove_found_types(removals, bd_dict)

        # Identification of Directional
        street_directional, match_key, bd_exceptions = find_directional(bd_dict)
        if match_key:
            removals.add(match_key)
            remove_found_types(removals, bd_dict)

        # Compile Body
        street_body = ' '.join(bd_dict.values())

        addr_deets = {'grid': grid_id, 'street_block': street_block, 'street_num': street_number,
                      'street_body': street_body, 'street_suffix': street_suffix,
                      'street_directional': street_directional, 'suite_num': addr_ste_num,
                      'box_num': box_num}

        return addr_deets, bd_exceptions


if __name__ == '__main__':
    # Test Scenario
    addr1 = Address('4568 East Gradine Drive SUITE J15', 'Seattle', 'WA', '98039')
    print(addr1)
    # Address('123B Main ST S', 'Seattle', 'WA', '98039')
    # Address('123 Main Street South Ste 58', 'Seattle', 'WA', '98039')
    # Address('110-10 Main ST S', 'Seattle', 'WA', '98039')
    # Address('123 N Carolina ST W', 'Seattle', 'WA', '98039')
