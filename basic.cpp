#include <string>
#include <vector>
#include <tuple>
#include <algorithm>
#include <iostream>

//
// Created by ishfaq on 21/02/2021.
//
// Digits constant which will be used to detect if an input character is a digit
const int DIGITS[] = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'};


// Error class
class Error{
public:
    explicit Error(int pos_start, int pos_end, std::string error_name, std::string details){
        this->pos_start = pos_start;
        this->pos_end = pos_end;
        this->error_name = error_name;
        this->details = details;
    }

    std::string message(){
        std::string message = error_name + ": " + details + "\n";
        message += "File" + std::to_string(pos_start.file_name) + ", line " + std::to_string(pos_start.line_num + 1);
        return message;
    }


public:
    int pos_start;
    int pos_end;
    std::string error_name;
    std::string details;
};

// Subclasses of the Error parent class for different error types
class IllegalCharError : public Error{
public:
    using Error::Error;  // Inherits the constructor from the parent class
    //(int pos_start, int pos_end, std::string error_name = "Illegal Character", std::string details)
};


// Position class
class Position{
public:
    Position(int index, int line_num, int col_num, std::string file_name, std::string file_text){
        this->index = index;
        this->line_num = line_num;
        this->col_num = col_num;
        this->file_name = file_name;
        this->file_text = file_text;
    }
    Position& advance(char current_char){
        index += 1;
        col_num += 1;

        if(current_char == '\n'){
            line_num += 1;
            col_num = 0;
        }
        return *this;
    }

    Position copy(){
        Position position(index, line_num, col_num, file_name, file_text);
        return position;
    }

public:
    int index;
    int line_num;
    int col_num;
    std::string file_name;
    std::string file_text;
};


// Token constants for the different token types
const std::string T_INT = "INT";
const std::string T_FLOAT = "FLOAT";
const std::string T_PLUS = "PLUS";
const std::string T_MINUS = "MINUS";
const std::string T_MUL = "MUL";
const std::string T_DIV = "DIV";
const std::string T_LBRAC = "LBRAC";
const std::string T_RBRAC = "RBRAC";


// Token class
class Token{
public:
    Token(std::string type, std::string value = ""){
        this->type = type;
        this->value = value;
    }

public:
    std::string type;
    std::string value;
};



// Lexer Class
class Lexer{
public:
    Lexer(std::string file_name, std::string text, Position pos) : pos(pos) {
        this->file_name= file_name;
        this->text= text;
        pos = Position(-1, 0, -1, file_name, text);
//        pos  = startPosition();
        this->current_char = 0;
        advance();
    }
//    Position startPosition(){
//        Position pos(-1, 0, -1, file_name, text);
//        return pos;
//    }
    void advance(){
        pos.advance(current_char);
        if(pos.index < text.length()){
            current_char = text[pos.index];
        }
        else{
            current_char = 0;
        }
    }

    std::tuple<std::vector<Token>, Error> make_tokens(){
        std::vector<Token> tokens;
        while(current_char != 0){
            if(current_char == ' ' || current_char == '\t'){
                advance();
            }
            else if(std::find(std::begin(DIGITS), std::end(DIGITS), (int) current_char) != std::end(DIGITS)){
                tokens.push_back(get_number());
            }
            else if(current_char == '+'){
                tokens.push_back(Token(T_PLUS));
                advance();
            }
            else if(current_char == '-'){
                tokens.push_back(Token(T_MINUS));
                advance();
            }
            else if(current_char == '*'){
                tokens.push_back(Token(T_MUL));
                advance();
            }
            else if(current_char == '/'){
                tokens.push_back(Token(T_DIV));
                advance();
            }
            else if(current_char == '('){
                tokens.push_back(Token(T_LBRAC));
                advance();
            }
            else if(current_char == ')'){
                tokens.push_back(Token(T_RBRAC));
                advance();
            }
            else{
                pos_start = pos.copy();
                character = current_char;
                advance();
                IllegalCharError err(pos_start, pos, '\'' + character + '\'');
                return std::tuple<std::vector<Token> = {}, IllegalCharError(pos_start, pos, '\'' + character + '\'')>;
            }
        }
        return std::tuple<tokens, IllegalCharError(pos_start, pos, '\'' + character + '\'')>;
    }

public:
    std::string file_name;
    std::string text;
    char current_char;
    Position pos;
    Position pos_start;
    char character;
};
