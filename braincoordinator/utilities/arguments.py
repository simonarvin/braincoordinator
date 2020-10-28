import argparse

class Arguments:
    def __init__(self, args):

        parsed_args = self.parse_args(args)
        self.animal = parsed_args.animal
        self.preload = parsed_args.preload
        self.reference = parsed_args.reference
        self.get = parsed_args.get

        print("Animal: {}".format(self.animal))
        print("Reference: {}".format(self.reference))

    def parse_args(self, args):
        parser = argparse.ArgumentParser()
        parser.add_argument('--animal', metavar='animal', default = "mouse_allen", required=False,
                            help='What animal to coordinate?')

        parser.add_argument('--reference', metavar='reference', default = "bregma", required=False,
                            help='What is your reference point? (bregma/lambda)')

        parser.add_argument('--preload', metavar='preload', default = 0, required=False,
                            help='Preload all slices?')

        parser.add_argument('--get', metavar='get', default = "", required=False,
                            help='Download atlas.')

        return parser.parse_args(args)
