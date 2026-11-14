`timescale 1ns/1ps


module alu_4bit(
    input [3:0] A,
    input [3:0] B,
    input [2:0] opcode,
    output reg carry,
    output reg zero,
    output reg [3:0] result
);

reg [4:0] temp;

always @(*) begin

    temp = 5'b00000;
    result = 4'b0000;
    carry = 1'b0;

    case(opcode)

        // ADD
        3'b000: begin
            temp = {1'b0, A} + {1'b0, B};
            result = temp[3:0];
            carry = temp[4];
        end

        // SUB
        3'b001: begin
            temp = {1'b0, A} + {1'b0, ~B} + 5'b00001;
            result = temp[3:0];
            carry = temp[4];
        end

        // AND
        3'b010: begin
            result = A & B;
            carry = 1'b0;
        end

        // OR
        3'b011: begin
            result = A | B;
            carry = 1'b0;
        end

        // XOR
        3'b100: begin
            result = A ^ B;
            carry = 1'b0;
        end

        // NOT A
        3'b101: begin
            result = ~A;
            carry = 1'b0;
        end

        // INCREMENT A
        3'b110: begin
            temp = {1'b0, A} + 5'b00001;
            result = temp[3:0];
            carry = temp[4];
        end

        // DECREMENT A
        3'b111: begin
            temp = {1'b0, A} + 5'b01111;
            result = temp[3:0];
            carry = temp[4];
        end

        default: begin
            result = 4'b0000;
            carry = 1'b0;
        end

    endcase

    // ZERO FLAG
    zero = (result == 4'b0000);

end

endmodule
