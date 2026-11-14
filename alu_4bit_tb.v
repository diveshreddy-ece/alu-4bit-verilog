`timescale 1ns/1ps

// Self-checking testbench for alu_4bit.
//  Phase 1: directed tests (one per opcode + flag edge cases), dumped to VCD.
//  Phase 2: exhaustive test of all 8 opcodes x 16 A x 16 B = 2048 combinations
//           against a behavioural reference model.
module alu_4bit_tb;

    reg [3:0] A, B;
    reg [2:0] opcode;

    wire [3:0] result;
    wire carry, zero;

    integer errors = 0;
    integer checks = 0;
    integer a, b, op;

    alu_4bit uut (
        .A(A),
        .B(B),
        .opcode(opcode),
        .result(result),
        .carry(carry),
        .zero(zero)
    );

    // Reference model: returns {carry, result}
    function [4:0] model(input [3:0] a, input [3:0] b, input [2:0] op);
        case (op)
            3'b000: model = a + b;                       // ADD
            3'b001: model = {1'b0, a} + {1'b0, ~b} + 1;  // SUB (carry = no borrow)
            3'b010: model = {1'b0, a & b};               // AND
            3'b011: model = {1'b0, a | b};               // OR
            3'b100: model = {1'b0, a ^ b};               // XOR
            3'b101: model = {1'b0, ~a};                  // NOT A
            3'b110: model = a + 1;                       // INC A
            3'b111: model = a + 4'b1111;                 // DEC A (carry = no borrow)
        endcase
    endfunction

    function [8*3-1:0] mnemonic(input [2:0] op);
        case (op)
            3'b000: mnemonic = "ADD";
            3'b001: mnemonic = "SUB";
            3'b010: mnemonic = "AND";
            3'b011: mnemonic = "OR ";
            3'b100: mnemonic = "XOR";
            3'b101: mnemonic = "NOT";
            3'b110: mnemonic = "INC";
            3'b111: mnemonic = "DEC";
        endcase
    endfunction

    task check(input verbose);
        reg [4:0] exp;
        begin
            exp = model(A, B, opcode);
            checks = checks + 1;
            if ({carry, result} !== exp || zero !== (exp[3:0] == 0)) begin
                errors = errors + 1;
                $display("FAIL  %s A=%b B=%b -> result=%b carry=%b zero=%b (expected %b %b %b)",
                         mnemonic(opcode), A, B, result, carry, zero,
                         exp[3:0], exp[4], exp[3:0] == 0);
            end else if (verbose)
                $display("PASS  %s A=%b(%2d) B=%b(%2d) -> result=%b(%2d) carry=%b zero=%b",
                         mnemonic(opcode), A, A, B, B, result, result, carry, zero);
        end
    endtask

    task apply(input [3:0] a_in, input [3:0] b_in, input [2:0] op_in);
        begin
            A = a_in; B = b_in; opcode = op_in;
            #5 check(1);
            #5;
        end
    endtask

    initial begin
        $dumpfile("alu_4bit.vcd");
        $dumpvars(0, alu_4bit_tb);

        $display("--- Directed tests ---");
        apply(4'd5,  4'd3, 3'b000); // ADD   5 + 3 = 8
        apply(4'd5,  4'd3, 3'b001); // SUB   5 - 3 = 2
        apply(4'd5,  4'd3, 3'b010); // AND
        apply(4'd5,  4'd3, 3'b011); // OR
        apply(4'd5,  4'd3, 3'b100); // XOR
        apply(4'd5,  4'd3, 3'b101); // NOT A
        apply(4'd5,  4'd3, 3'b110); // INC A
        apply(4'd5,  4'd3, 3'b111); // DEC A
        apply(4'd15, 4'd1, 3'b000); // ADD overflow: 15 + 1 -> 0, carry, zero
        apply(4'd5,  4'd5, 3'b001); // SUB zero flag: 5 - 5 = 0
        apply(4'd3,  4'd5, 3'b001); // SUB borrow: 3 - 5 -> 14, carry = 0
        apply(4'd0,  4'd0, 3'b111); // DEC underflow: 0 - 1 -> 15, carry = 0
        $dumpoff;

        $display("--- Exhaustive test (all opcodes, all A, all B) ---");
        for (op = 0; op < 8; op = op + 1)
            for (a = 0; a < 16; a = a + 1)
                for (b = 0; b < 16; b = b + 1) begin
                    A = a; B = b; opcode = op;
                    #1 check(0);
                end

        if (errors == 0)
            $display("ALL TESTS PASSED (%0d/%0d checks)", checks, checks);
        else
            $display("%0d of %0d CHECKS FAILED", errors, checks);
        $finish;
    end

endmodule
