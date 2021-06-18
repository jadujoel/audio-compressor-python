import sys
import shutil
import numpy as np
np.set_printoptions(precision=1)
class Repr:
    def __init__(self, cls=None):
        if cls is not None:
            self.__dict__.update(cls.__dict__)

    def __repr__(self):
        return self.print()

    def __sizeof__(self):
        size = 0
        for k, v in self.__dict__.items():
            size += sys.getsizeof(v)
        return size

    # def get_size(self, obj, seen=None):
    #     """Recursively finds size of objects"""
    #     size = sys.getsizeof(obj)
    #     if seen is None:
    #         seen = set()
    #     obj_id = id(obj)
    #     if obj_id in seen:
    #         return 0
    #     # Important mark as seen *before* entering recursion to gracefully handle
    #     # self-referential objects
    #     seen.add(obj_id)
    #     if isinstance(obj, dict):
    #         size += sum([self.get_size(v, seen) for v in obj.values()])
    #         size += sum([self.get_size(k, seen) for k in obj.keys()])
    #     elif hasattr(obj, '__dict__'):
    #         size += self.get_size(obj.__dict__, seen)
    #     elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
    #         size += sum([self.get_size(i, seen) for i in obj])
    #     return size

    def print(self):
        table = self.format_dictionary_for_print(self.__dict__)

        if '__name__' in dir(self):
            name = self.__name__
        else:
            name = str(type(self))#[17:-2]

        head = f'{name} of size {self.humanbytes(self._total_size)}'

        return f'{head}\n{table}'

    def humanbytes(self, bytes_):
            """ Return the given bytes as a human friendly KB, MB, GB, or TB string """
            bytes_ = float(bytes_)
            kiloBytes = float(1024)
            megaBytes = float(kiloBytes ** 2) # 1,048,576
            gigaBytes = float(kiloBytes ** 3) # 1,073,741,824
            terraBytes = float(kiloBytes ** 4) # 1,099,511,627,776

            if bytes_ < kiloBytes:
                return f'{int(bytes_)} B'
            elif kiloBytes <= bytes_ < megaBytes:
               return f'{int(bytes_/kiloBytes)} KB'
            elif megaBytes <= bytes_ < gigaBytes:
               return f'{int(bytes_/megaBytes)} MB'
            elif gigaBytes <= bytes_ < terraBytes:
               return f'{int(bytes_/gigaBytes)} GB'
            elif terraBytes <= bytes_:
               return f'{int(bytes_/terraBytes)} TB'

    def space(self, thing, target_len):
        space = ' '*(target_len-len(thing)-2)
        return f' {thing}{space}|'

    def format_dictionary_for_print(self, _dict):
        width, height = shutil.get_terminal_size()
        max_byte_size_to_print = 102400
        max_line_width = width

        _type_target_len = int(width*0.08)#10
        _size_target_len = 9
        _key_target_len = int(width*0.2)
        _value_target_len = max_line_width - _type_target_len - _size_target_len - _key_target_len

        space = ' '
        _divider = '_'*max_line_width
        _overline = r'‾'*max_line_width

        _x = {'Type':_type_target_len, 'Size':_size_target_len, 'Key':_key_target_len, 'Value':_value_target_len}
        _header = ''.join([self.space(k, v) for k, v in _x.items()])[:-1]

        _table = (
            f'{_divider}\n'
            f'{_header}'
            )

        self._total_size = 0
        for key, value in _dict.items():

            # Keys
            _key = str(key)

            # Types
            _type = str(type(value))[8:-2]
            if _type.startswith('numpy'):
                _type = f'np{_type[5:]}'
            if _type.endswith('array'):
                _type = f'{_type[:-5]}arr'
            if _type == 'NoneType':
                _type = 'None'

            # Sizes
            if self.is_class(value):
                #_size_in_bytes = self.get_size(value)
                _size_in_bytes = 0
                for k, v in value.__dict__.items():
                    _size_in_bytes += sys.getsizeof(value)
            elif self.is_list_of_classes(value):
                _size_in_bytes = 0
                for item in value:
                    for k, v in item.__dict__.items():
                        _size_in_bytes += sys.getsizeof(v)
            else:
                _size_in_bytes = sys.getsizeof(value)

            _size = self.humanbytes(_size_in_bytes)

            self._total_size += _size_in_bytes

            # Values
            if _size_in_bytes > max_byte_size_to_print:
                if isinstance(value, np.ndarray):
                    _value = f"shape=({str(','.join([str(v) for v in value.shape]))})"
                    if self.is_numbers(value):
                        _value += f' minmax={np.min(value):.1f},{np.max(value):.1f}'

                elif self.is_list_of_classes(value):
                    clas = ','.join([str(type(xn))[17:-2] for xn in value])
                    _value = f'objlist: {clas}'

                else:
                    _value = str(value)#'... !! ...'

            else:
                if self.is_class(value):
                    _value = f'class: {str(type(value))[17:-2]}'
                elif isinstance(value, (list, np.ndarray)):
                    if self.is_list_of_classes(value):
                        _value = 'classes:' + ','.join([str(type(xn))[17:-2] for xn in value])
                    else: _value = str(value)
                else:
                    _value = str(value)

            _value = _value.replace('\n', '').replace('\r', '')
            if len(_value) > _value_target_len:
                _value = f'{_value[:(_value_target_len//2)-6]} ... {_value[-(_value_target_len//2):]}'

            if len(_key) > _key_target_len-2:
                _key = _key[:_key_target_len-4] + '..'

            if len(_type) > _type_target_len-2:
                _type = _type[:_type_target_len-4] + '..'

            _type_spaces_to_add = _type_target_len - len(_type)-2
            _type_spaces_end = _type_spaces_to_add
            _type_spaces =  space * _type_spaces_to_add
            _type_formatted = _type + _type_spaces

            _size_spaces_to_add = _size_target_len - len(_size)-2
            _size_spaces_end = _size_spaces_to_add
            _size_spaces =  space * _size_spaces_to_add
            _size_formatted = _size + _size_spaces

            _key_spaces_to_add = _key_target_len - len(_key)-2
            _key_spaces_end = _key_spaces_to_add
            _key_spaces =  space * _key_spaces_to_add
            _key_formatted = _key + _key_spaces

            _value_spaces_to_add = _value_target_len - len(_value)-2
            _value_spaces_end = _value_spaces_to_add
            _value_spaces =  space * _value_spaces_to_add
            _value_formatted = _value + _value_spaces

            new_line = f'\n {_type_formatted}| {_size_formatted}| {_key_formatted}| {_value_formatted}'
            _table = _table + new_line

        _table = _table + f'\n{_overline}'
        return _table

    def is_list(self, thing):
        return isinstance(thing, (list, np.ndarray))

    def is_class(self, thing):
        return str(type(thing)).startswith("<class '__main__.")

    def is_list_of_classes(self, thing):
        if not self.is_list(thing): return False
        else: return all([str(type(x)).startswith("<class '__main__.") for x in thing])

    def is_numbers(self, thing):
        _dtype = np.array(list(thing)).dtype
        return str(
            _dtype).startswith('int') or str(
            _dtype).startswith('float') or str(
            _dtype).startswith('complex'
            )

