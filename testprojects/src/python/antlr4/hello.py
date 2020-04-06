from antlr4 import InputStream, CommonTokenStream, ParseTreeWalker
from pants_antlr4.test.eval.HelloLexer import HelloLexer
from pants_antlr4.test.eval.HelloListener import HelloListener
from pants_antlr4.test.eval.HelloParser import HelloParser
import sys


class HelloPrintListener(HelloListener):
    def enterHi(self, ctx):
        print("You are greeting: %s" % ctx.ID())


def main():
    char_stream = InputStream("{}\n".format(sys.argv[1]))
    lexer = HelloLexer(char_stream)
    tokens = CommonTokenStream(lexer)
    parser = HelloParser(tokens)

    tree = parser.hi()
    printer = HelloPrintListener()
    walker = ParseTreeWalker()
    walker.walk(printer, tree)


if __name__ == "__main__":
    main()
