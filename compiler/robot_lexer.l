%{
/*
 * ============================================================
 *  robot_lexer.l  --  Flex Lexical Analyser
 *  Robot Command Language (RCL)
 *
 *  Tokens produced:
 *    MOVE, FORWARD, BACKWARD, LEFT, RIGHT, TURN,
 *    STOP, ABILITY, SPEED, STEPS, DEGREES,
 *    NUMBER  (integer or float),
 *    STRING  (double-quoted text)
 *
 *  Ignored:
 *    Whitespace, newlines, single-line comments ( # ... )
 *
 *  Aliases supported (case-insensitive):
 *    go -> MOVE,  rotate -> TURN,  halt -> STOP
 *    back -> BACKWARD,  skill -> ABILITY
 *    step -> STEPS,  degree/deg -> DEGREES
 *
 *  Build:
 *    flex robot_lexer.l          (produces lex.yy.c)
 *    See Makefile for full build.
 * ============================================================
 */

#include "robot_parser.tab.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int line_num = 1;
%}

%option noyywrap
%option yylineno
%option case-insensitive

DIGIT       [0-9]
INTEGER     {DIGIT}+
FLOAT       {DIGIT}+"."{DIGIT}+
NUMBER      {FLOAT}|{INTEGER}
WHITESPACE  [ \t\r]+
NEWLINE     \n
STRING      \"[^\"]*\"
COMMENT     #[^\n]*

%%

"move"          { return MOVE;     }
"go"            { return MOVE;     }

"forward"       { return FORWARD;  }
"backward"      { return BACKWARD; }
"back"          { return BACKWARD; }

"left"          { return LEFT;     }
"right"         { return RIGHT;    }

"turn"          { return TURN;     }
"rotate"        { return TURN;     }

"stop"          { return STOP;     }
"halt"          { return STOP;     }

"ability"       { return ABILITY;  }
"skill"         { return ABILITY;  }

"speed"         { return SPEED;    }

"steps"         { return STEPS;    }
"step"          { return STEPS;    }
"degrees"       { return DEGREES;  }
"degree"        { return DEGREES;  }
"deg"           { return DEGREES;  }

{NUMBER}        {
                    yylval.fval = atof(yytext);
                    return NUMBER;
                }

{STRING}        {
                    char *s = strdup(yytext + 1);
                    s[strlen(s) - 1] = '\0';
                    yylval.sval = s;
                    return STRING;
                }

{COMMENT}       { /* skip comments */ }
{WHITESPACE}    { /* skip whitespace */ }
{NEWLINE}       { line_num++; }

.               {
                    fprintf(stderr,
                        "Lexer Error (line %d): unknown character '%s'\n",
                        line_num, yytext);
                }

%%
