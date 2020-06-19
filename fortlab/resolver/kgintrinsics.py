
Intrinsic_Procedures = [ \
# numeric functions \
'abs','aimag','aint','anint','ceiling','cmplx','conjg','dble','dim','dprod','floor','int','max','min','mod','modulo','nint','real','sign', \
# mathematical functions \
'acos','asin','atan','atan2','cos','cosh','exp','log','log10','sin','sinh','sqrt','tan','tanh', \
# character functions \
'achar','adjustl','adjustr','char','iachar','ichar','index','len_trim','lge','lgt','lle','llt','max','min','repeat','scan','trim','verify', \
# kind functions \
'kind','selected_char_kind','selected_int_kind','selected_real_kind', \
# miscellaneous type conversion functions \
'logical', 'transfer', \
# numeric inquiry functions \
'digits','epsilon','huge','maxexponent','minexponent','precision','radix','range','tiny', \
# array inquiry functions \
'lbound','shape','size','ubound', \
# other inquiry functions \
'allocated','associated','bit_size','extends_type_of','len','new_line','present','same_type_as', \
# bit manipulation procedures \
'btest','iand','ibclr','ibits','ibset','ieor','ior','ishft','ishftc','mvbits','not', \
# vector and matrix multiply functions \
'exponent','fraction','nearest','rrspacing','scale','set_exponent','spacing','dot_product','matmul', \
# array reduction functions \
'all' ,'any' ,'count' ,'maxval' ,'minval' ,'product' ,'sum', \
# array construction functions \
'cshift','eoshift','merge','pack','reshape','spread','transpose','unpack', \
# array location functions \
'maxloc','minloc', \
# null function \
'null', \
# allocation transfer procedure \
'move_alloc', \
# random number subroutines \
'random_number','random_seed', \
# system environment procedures \
'command_argument_count','cpu_time','date_and_time','get_command','get_command_argument','get_environment_variable','is_iostat_end','is_iostat_eor','system_clock', \
# specific names \
'alog','alog10','amax0','amax1','amin0','amin1','amod','cabs','ccos','cexp','clog','csin','csqrt','dabs','dacos','dasin','datan','dcos','dcosh','ddim','dexp','dint','dlog','dlog10','dmax1','dmin1','dmod','dnint','dsign','dsin','dsinh','dsqrt','dtan','dtanh','float','iabs','idim','idint','idnint','ifix','isign','max0','max1','min0','min1' \
]

Intrinsic_Modules = { \
    'ISO_FORTRAN_ENV': [ 'error_unit', 'file_storage_size', 'input_unit', 'iostat_end', 'iostat_eor', 'numeric_storage_size', 'output_unit', 'character_storage_size' ], \
    'ISO_C_BINDING': [ 'c_associated', 'c_f_pointer', 'c_f_procpointer', 'c_funloc', 'c_loc', 'c_sizeof', 'c_int', 'c_short', 'c_long', 'c_long_long', 'c_signed_char', 'c_size_t', 'c_int8_t', 'c_int16_t', 'c_int32_t', 'c_int64_t', 'c_int_least8_t', 'c_int_least16_t', 'c_int_least32_t', 'c_int_least64_t', 'c_int_fast8_t', 'c_int_fast16_t', 'c_int_fast32_t', 'c_int_fast64_t', 'c_intmax_t', 'c_intptr_t', 'c_ptrdiff_t', 'c_float', 'c_double', 'c_long_double', 'c_float_complex', 'c_double_complex', 'c_long_double_complex', 'c_bool', 'c_char', 'c_null_char', 'c_alert', 'c_backspace', 'c_form_feed', 'c_new_line', 'c_carriage_return', 'c_horizontal_tab', 'c_vertical_tab', 'c_null_ptr', 'c_ptr', 'c_null_funptr', 'c_funptr ' ], \
    'IEEE_EXCEPTIONS': [ 'ieee_flag_type', 'ieee_status_type', 'ieee_support_flag', 'ieee_support_halting', 'ieee_get_flag', 'ieee_get_halting_mode', 'ieee_get_status', 'ieee_set_flag', 'ieee_set_halting_mode', 'ieee_set_status' ], \
    'IEEE_ARITHMETIC': [ 'ieee_class_type', 'ieee_round_type', 'ieee_support_datatype', 'ieee_support_divide', 'ieee_support_denormal', 'ieee_support_inf', 'ieee_support_io', 'ieee_support_nan', 'ieee_support_rounding', 'ieee_support_standard', 'ieee_support_underflow_control', 'ieee_support_sqrt', 'ieee_class', 'ieee_copy_sign', 'ieee_is_finite', 'ieee_is_nan', 'ieee_is_normal', 'ieee_is_negative', 'ieee_is_logb', 'ieee_next_after', 'ieee_rem', 'ieee_rint', 'ieee_scalb', 'ieee_unordered', 'ieee_value', 'ieee_selected_real_kind', 'ieee_get_rounding_mode', 'ieee_get_underflow_mode', 'ieee_set_rounding_mode', 'ieee_set_underflow_mode' ], \
    'IEEE_FEATURES': [ 'ieee_features_type' ] \
}

