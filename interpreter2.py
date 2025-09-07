import re, random

# ---------------- Funny messages ----------------
FUNNY = [
    "Gandu! code thik kor na.",
    "Arre honuman! kichu ulta palta paisi.",
    "Bokachondro matha mota, abar try kor.",
]

# ---------------- Lexer ----------------
KEYWORDS = {
    "bol":"PRINT","jodi":"IF","naile":"ELSE","jotokhon":"WHILE",
    "ghurche":"FOR","dhoro":"LET","kaj":"FUNC","phire":"RETURN",
    "thik":"TRUE","dhop":"FALSE","Likh":"INPUT",
    "shuru":"BEGIN","ses":"END"
}

TOKEN_SPEC = [
    ("NUMBER",  r"\d+"),
    ("STRING",  r'"[^"]*"'),
    ("IDENT",   r"[A-Za-z_][A-Za-z0-9_]*"),
    ("OP",      r"[+\-*/%=<>!]+"),  # <-- added % here
    ("LPAREN",  r"\("),
    ("RPAREN",  r"\)"),
    ("LBRACE",  r"\{"),
    ("RBRACE",  r"\}"),
    ("COMMA",   r","),
    ("SEMICOL", r";"),
    ("NEWLINE", r"\n"),
    ("SKIP",    r"[ \t]+"),
    ("MISMATCH",r"."), 
]

tok_regex = "|".join("(?P<%s>%s)" % pair for pair in TOKEN_SPEC)
get_token = re.compile(tok_regex).match

def lex(code):
    pos = 0; toks=[]
    while pos < len(code):
        m = get_token(code,pos)
        if not m: raise SyntaxError("Invalid token near: "+code[pos:])
        kind = m.lastgroup; val = m.group()
        if kind=="NUMBER": toks.append(("NUMBER",int(val)))
        elif kind=="STRING": toks.append(("STRING",val.strip('"')))
        elif kind=="IDENT":
            if val in KEYWORDS: toks.append((KEYWORDS[val],val))
            else: toks.append(("IDENT",val))
        elif kind=="SKIP" or kind=="NEWLINE": pass
        elif kind=="MISMATCH": raise SyntaxError("Illegal char: "+val)
        else: toks.append((kind,val))
        pos=m.end()
    toks.append(("EOF",""))
    return toks

# ---------------- Parser ----------------
class Parser:
    def __init__(self,toks): self.toks=toks; self.pos=0
    def peek(self): return self.toks[self.pos]
    def eat(self,kind=None):
        tok=self.toks[self.pos]; self.pos+=1
        if kind and tok[0]!=kind: raise SyntaxError(random.choice(FUNNY))
        return tok

    def parse(self):
        prog=[]
        while self.peek()[0]!="EOF": prog.append(self.stmt())
        return ("BLOCK",prog)

    def stmt(self):
        tok=self.peek()[0]
        if tok=="PRINT":
            self.eat("PRINT"); expr=self.expr()
            return ("PRINT",expr)
        if tok=="LET":
            self.eat("LET"); name=self.eat("IDENT")[1]; self.eat("OP")
            expr=self.expr(); return ("LET",name,expr)
        if tok=="IDENT":
            name=self.eat("IDENT")[1]; self.eat("OP"); expr=self.expr()
            return ("SET",name,expr)
        if tok=="IF":
            self.eat("IF"); cond=self.expr(); self.eat("LBRACE")
            then=self.parse_block(); self.eat("RBRACE")
            els=None
            if self.peek()[0]=="ELSE":
                self.eat("ELSE"); self.eat("LBRACE")
                els=self.parse_block(); self.eat("RBRACE")
            return ("IF",cond,then,els)
        if tok=="WHILE":
            self.eat("WHILE"); cond=self.expr(); self.eat("LBRACE")
            body=self.parse_block(); self.eat("RBRACE")
            return ("WHILE",cond,body)
        if tok=="FOR":
            self.eat("FOR")
            if self.peek()[0]=="LET":
                self.eat("LET"); name=self.eat("IDENT")[1]; self.eat("OP")
                init=("LET",name,self.expr())
            elif self.peek()[0]=="IDENT":
                name=self.eat("IDENT")[1]; self.eat("OP")
                init=("SET",name,self.expr())
            else: raise SyntaxError("Invalid for-loop init")
            self.eat("SEMICOL")
            cond=self.expr(); self.eat("SEMICOL")
            if self.peek()[0]=="IDENT":
                name=self.eat("IDENT")[1]; self.eat("OP")
                update=("SET",name,self.expr())
            else: raise SyntaxError("Invalid for-loop update")
            self.eat("LBRACE"); body=self.parse_block(); self.eat("RBRACE")
            return ("FOR",init,cond,update,body)
        if tok=="FUNC":
            self.eat("FUNC"); name=self.eat("IDENT")[1]
            self.eat("LPAREN"); params=[]
            if self.peek()[0]!="RPAREN":
                params.append(self.eat("IDENT")[1])
                while self.peek()[0]=="COMMA":
                    self.eat("COMMA"); params.append(self.eat("IDENT")[1])
            self.eat("RPAREN"); self.eat("LBRACE")
            body=self.parse_block(); self.eat("RBRACE")
            return ("FUNC",name,params,body)
        if tok=="RETURN":
            self.eat("RETURN"); expr=self.expr()
            return ("RETURN",expr)
        if tok=="BEGIN":
            self.eat("BEGIN"); body=self.parse_block(); self.eat("END")
            return ("BLOCK",body)
        return ("EXPR",self.expr())

    def parse_block(self):
        stmts=[]
        while self.peek()[0] not in ("RBRACE","END","EOF"):
            stmts.append(self.stmt())
        return stmts

    # ---- Expressions ----
    def expr(self):
        node=self.term()
        while self.peek()[0]=="OP" and self.peek()[1] in ("+","-","<",">","=="):
            op=self.eat("OP")[1]; right=self.term(); node=("BINOP",op,node,right)
        return node
    def term(self):
        node=self.factor()
        while self.peek()[0]=="OP" and self.peek()[1] in ("*","/","%"):  # <-- added %
            op=self.eat("OP")[1]; right=self.factor(); node=("BINOP",op,node,right)
        return node
    def factor(self):
        tok=self.peek()
        if tok[0]=="NUMBER": self.eat("NUMBER"); return ("NUM",tok[1])
        if tok[0]=="STRING": self.eat("STRING"); return ("STR",tok[1])
        if tok[0]=="IDENT":
            name=self.eat("IDENT")[1]
            if self.peek()[0]=="LPAREN":
                self.eat("LPAREN"); args=[]
                if self.peek()[0]!="RPAREN":
                    args.append(self.expr())
                    while self.peek()[0]=="COMMA":
                        self.eat("COMMA"); args.append(self.expr())
                self.eat("RPAREN"); return ("CALL",name,args)
            return ("VAR",name)
        if tok[0]=="TRUE": self.eat("TRUE"); return ("BOOL",True)
        if tok[0]=="FALSE": self.eat("FALSE"); return ("BOOL",False)
        if tok[0]=="INPUT": self.eat("INPUT"); return ("INPUT",)
        if tok[0]=="LPAREN":
            self.eat("LPAREN"); node=self.expr()
            if self.peek()[0]!="RPAREN": raise SyntaxError("Missing closing parenthesis ')'")
            self.eat("RPAREN"); return node
        raise SyntaxError(random.choice(FUNNY))

# ---------------- Interpreter ----------------
class Env(dict):
    def __init__(self,parent=None): 
        super().__init__(); self.parent=parent

    def get(self,name):
        if name in self: return self[name]
        if self.parent: return self.parent.get(name)
        raise NameError(f'tor "{name}" koi re bokachondro, age seta likh bhai!!')

def eval_node(node,env):
    t=node[0]
    if t=="BLOCK":
        res=None
        for st in node[1]:
            res=eval_node(st,env)
            if isinstance(res,tuple) and res[0]=="RETURN": return res
        return res
    if t=="PRINT":
        val=eval_node(node[1],env)
        print(val)
        return val
    if t=="LET":
        env[node[1]]=eval_node(node[2],env); return env[node[1]]
    if t=="SET":
        env.get(node[1]); env[node[1]]=eval_node(node[2],env); return env[node[1]]
    if t=="IF":
        cond=eval_node(node[1],env)
        if cond: return eval_node(("BLOCK",node[2]),Env(env))
        elif node[3]: return eval_node(("BLOCK",node[3]),Env(env))
        return None
    if t=="WHILE":
        while eval_node(node[1],env):
            res = eval_node(("BLOCK",node[2]), env)
            if isinstance(res, tuple) and res[0]=="RETURN": return res
        return None
    if t=="FOR":
        eval_node(node[1],env)
        while eval_node(node[2],env):
            res=eval_node(("BLOCK",node[4]),env)
            if isinstance(res, tuple) and res[0]=="RETURN": return res
            eval_node(node[3],env)
        return None
    if t=="FUNC":
        env[node[1]]=("FUNC",node[2],node[3]); return None
    if t=="CALL":
        func=env.get(node[1])
        if func[0]=="FUNC":
            _,params,body=func; new=Env(env)
            for p,a in zip(params,node[2]): new[p]=eval_node(a,env)
            res=eval_node(("BLOCK",body),new)
            if isinstance(res,tuple) and res[0]=="RETURN": return res[1]
            return res
        raise NameError("Unknown func "+node[1])
    if t=="RETURN": return ("RETURN",eval_node(node[1],env))
    if t=="BINOP":
        l=eval_node(node[2],env); r=eval_node(node[3],env)
        if node[1]=="+" and (isinstance(l,str) or isinstance(r,str)): return str(l)+str(r)
        if node[1]=="+": return l+r
        if node[1]=="-": return l-r
        if node[1]=="*": return l*r
        if node[1]=="/": return l//r
        if node[1]=="%": return l % r       # <-- modulus
        if node[1]=="<": return l<r
        if node[1]==">": return l>r
        if node[1]=="==": return l==r
    if t=="NUM": return node[1]
    if t=="STR": return node[1]
    if t=="VAR": return env.get(node[1])
    if t=="BOOL": return node[1]
    if t=="INPUT": return input("Likh: ")

def run(src):
    toks=lex(src); parser=Parser(toks); tree=parser.parse()
    env=Env(); eval_node(tree,env)
