import sys
import uuid
import yaml
import copy
import logging
import pathlib
import hashlib
from typing import Any, Dict, List, Sequence, Union
from pathlib import Path

class NameSpaces:

    def __str__(self) -> str:
        return self.__retrieve(self.__dict__)
    
    def __retrieve(self, kws: dict, deep:int=0):
        string = ""
        for key, items in kws.items():
            string += " \n{}{}".format('   '*deep, key)
            if isinstance(items, NameSpaces):
                items = self.__retrieve(items.__dict__, deep+1)

            string += " {}".format(items)
        return string
    
    def __todict(self, kws: dict):
        kw_dict = {}
        for key, items in kws.items():
            if isinstance(items, NameSpaces):
                items = self.__todict(items.__dict__)
            elif isinstance(items, (bool, int, float, str, dict, list, tuple)):
                ...
            else:
                items = str(items)

            kw_dict[key] = items
        return kw_dict
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.__todict(self.__dict__)
    
    


class YamlParser:
    def __init__(self) -> None:
        self.tree = {} # save parse tree
        self.args = {} # save arguments
        self.__basic_namespaces = NameSpaces()
        self.name_spaces = None

    def add_argument(self, *args:List[str], default=None, dtype=None, choices:Sequence[Any]=None):
        # support argments:
        #  -x
        #  -xxx
        #  -xxx.xxx
        arg_id = uuid.uuid1(self.args.__len__()).int
        self.args[arg_id] = {"default": default, "dtype":dtype, "choices":choices}

        for arg in args:
            arg: str
            if arg.startswith('-'):
                arg = arg.removeprefix('-')
            else:
                raise ValueError("Argument must start with -", arg)
            
            str_hash = arg.__hash__()
            self.tree[str_hash] = arg_id

            if '.' in arg:
                options = arg.split('.')
                basic_c =  self.__basic_namespaces
                for opt in options[:-1]:
                    if hasattr(basic_c, opt):
                        ...
                    else:
                        basic_c.__setattr__(opt, NameSpaces())
                    basic_c = getattr(basic_c, opt)
                basic_c.__setattr__(options[-1], default)
            else:
                if hasattr(self.__basic_namespaces, arg):
                    ...
                else:
                    self.__basic_namespaces.__setattr__(arg, default)

    
    def parse_args(self, args: Dict[str, Any]=None, config_files: Sequence[str] = None):
        """_summary_

        Args:
            args (Dict[str, Any], optional): _description_. Defaults to None.
            config_files (Sequence[str], optional): _description_. Defaults to None.

        Raises:
            TypeError: _description_
            TypeError: _description_

        Returns:
            _type_: _description_
        """
        self.name_spaces = copy.deepcopy(self.__basic_namespaces)
        
        if config_files is None:
            ...
        elif isinstance(config_files, str):
            self.__read_config(file)
        elif isinstance(config_files, (list, tuple)):
            for file in config_files:    
                self.__read_config(file)
        else:
            raise TypeError(config_files)
        
        if args is None:
            ...
        elif isinstance(args, dict):
            self.__parser_dict_config(args)
        else:
            raise TypeError(args)

        return self.name_spaces
    
    def update(self, path: Union[str, pathlib.Path]):
        if self.name_spaces is None:
            self.name_spaces = copy.deepcopy(self.__basic_namespaces)
            
        if isinstance(path, str):
            path = pathlib.Path(path)
        elif isinstance(path, pathlib.Path):
            ...
        else:
            raise TypeError(path)
        
        if not path.exists():
            raise FileExistsError(path)
        
        self.__read_config(path)

        return self.name_spaces

    def __read_config(self, file: Union[str, Path]):
        if isinstance(file, str):
            file = pathlib.Path(file)
        elif isinstance(file, Path):
            ...
        else:
            raise TypeError(file)

        with file.open('r', encoding='utf-8') as f:
            config = yaml.load(f.read(), Loader=yaml.FullLoader)
        self.__parser_dict_config(config)
        

    def __parser_dict_config(self, config: dict, parents=None):
        for key, value in config.items():
            if isinstance(value, dict):
                if parents is not None:
                    parent = '.'.join([parents, key])
                else:
                    parent = key
                self.__parser_dict_config(value, parent)
            else:
                if parents is not None:
                    args_key = '.'.join([parents, key])
                else:
                    args_key = key
                self.__parser_config(args_key, value)
                
    def __parser_config(self, key: str, value):
        str_hash = key.__hash__()
        arg_hash = self.tree.get(str_hash)
        if arg_hash is None:
            logging.warning("Unknown {}".format(key))
            return
        else:
            arg_action = self.args[arg_hash]
            
            dtype = arg_action.get('dtype')
            if dtype:
                if isinstance(value, dtype):
                    ...
                else:
                    value = dtype(value)
            
            choices = arg_action.get("choices")
            if choices:
                if isinstance(choices, (list, tuple)):
                    if value in choices:
                        ...
                    elif value is None:
                        ...
                    else:
                        logging.error("argument {}: invalid choice: '{}' (choose from {})".format(key, value, choices))
                        sys.exit(-1)
                else:
                    raise TypeError(key, "choice", choices)
            
            basic_c =  self.name_spaces
            if '.' in key:
                options = key.split('.')
                for opt in options[:-1]:
                    basic_c = getattr(basic_c, opt)
                opt = options[-1]
            else:
                opt = key

            basic_c.__setattr__(opt, value)

    def write(self, path: Union[str, pathlib.Path], config: NameSpaces=None):
        if config is None:
            config = self.name_spaces

        if isinstance(path, str):
            path = pathlib.Path(path)
        elif isinstance(path, pathlib.Path):
            ...
        else:
            raise TypeError(path)
        
        with path.open('w', encoding='utf-8') as f:
            yaml.dump(config(), f)
            logging.info("Dump config into {}".format(path))
                