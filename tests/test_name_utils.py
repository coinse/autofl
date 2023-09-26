from lib import name_utils

def test_drop_base_name():
    assert name_utils.drop_base_name("a.b.c") == "a.b"

def test_get_base_name():
    assert name_utils.get_base_name("a.b.c") == "c"
    assert name_utils.get_base_name("c") == "c"

def test_parse_arguments():
    assert name_utils.parse_arguments("com.google.common.base.Supplier<java.util.List<com.google.javascript.jscomp.SourceFile>>, com.google.common.base.Supplier<java.util.List<com.google.javascript.jscomp.SourceFile>>, com.google.common.base.Supplier<java.util.List<com.google.javascript.jscomp.JSModule>>, com.google.common.base.Function<java.lang.Integer, java.lang.Boolean>") == [
        'com.google.common.base.Supplier<java.util.List<com.google.javascript.jscomp.SourceFile>>',
        'com.google.common.base.Supplier<java.util.List<com.google.javascript.jscomp.SourceFile>>',
        'com.google.common.base.Supplier<java.util.List<com.google.javascript.jscomp.JSModule>>',
        'com.google.common.base.Function<java.lang.Integer, java.lang.Boolean>'
    ]

    assert name_utils.parse_arguments("java.lang.String, java.util.Locale, java.util.Map<java.lang.String, ? extends org.apache.commons.lang3.text.FormatFactory>") == [
        "java.lang.String",
        "java.util.Locale",
        "java.util.Map<java.lang.String, ? extends org.apache.commons.lang3.text.FormatFactory>"
    ]

    assert name_utils.parse_arguments('T, org.apache.commons.lang3.builder.ToStringStyle, java.lang.StringBuffer, java.lang.Class<? super T>, boolean[], boolean') == [
        "T",
        "org.apache.commons.lang3.builder.ToStringStyle",
        "java.lang.StringBuffer", "java.lang.Class<? super T>",
        "boolean[]",
        "boolean"
    ]

def test_get_method_name_and_argument_types():
    signature = "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator()"
    method_name, arg_types = name_utils.get_method_name_and_argument_types(signature)
    assert method_name == ['org', 'apache', 'commons', 'lang3', 'text', 'translate', 'LookupTranslator', 'LookupTranslator']
    assert arg_types == []

    signature = "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(int)"
    method_name, arg_types = name_utils.get_method_name_and_argument_types(signature)
    assert method_name == ['org', 'apache', 'commons', 'lang3', 'text', 'translate', 'LookupTranslator', 'LookupTranslator']
    assert arg_types == ['int']

    signature = "org.apache.commons.lang3.text.translate.LookupTranslator.<init>(int)"
    method_name, arg_types = name_utils.get_method_name_and_argument_types(signature)
    assert method_name == ['org', 'apache', 'commons', 'lang3', 'text', 'translate', 'LookupTranslator', 'LookupTranslator']
    assert arg_types == ['int']

    signature = "org.apache.commons.lang3.text.ExtendedMessageFormat.ExtendedMessageFormat(java.lang.String, java.util.Locale, java.util.Map<java.lang.String, ? extends org.apache.commons.lang3.text.FormatFactory>)"
    method_name, arg_types = name_utils.get_method_name_and_argument_types(signature)
    assert method_name == ['org','apache','commons','lang3','text','ExtendedMessageFormat','ExtendedMessageFormat']
    assert arg_types == ['String', 'Locale', 'Map<String, ? extends FormatFactory>']

    signature = "org.apache.commons.lang3.text.ExtendedMessageFormat.ExtendedMessageFormat(java.lang.String arg1, java.util.Locale arg2, java.util.Map<java.lang.String, ? extends org.apache.commons.lang3.text.FormatFactory> arg3)"
    method_name, arg_types = name_utils.get_method_name_and_argument_types(signature)
    assert method_name == ['org','apache','commons','lang3','text','ExtendedMessageFormat','ExtendedMessageFormat']
    assert arg_types == ['String', 'Locale', 'Map<String, ? extends FormatFactory>']

def test_get_method_name():
    signature = "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(int)"
    assert name_utils.get_method_name(signature) == "LookupTranslator"
    assert name_utils.get_method_name(signature, simple_name=False) == "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator"

def test_name_matcher():
    assert name_utils.name_matcher(["Object"], ["java", "lang", "Object"])
    assert name_utils.name_matcher(["Object"], ["lang", "Object"])
    assert name_utils.name_matcher(["Object"], ["Object"])
    assert not name_utils.name_matcher(["java", "Object"], ["java", "lang", "Object"])
    assert not name_utils.name_matcher(["bject"], ["java", "lang", "Object"])
    assert not name_utils.name_matcher(["ang", "Object"], ["java", "lang", "Object"])

def test_lenient_matcher_exact_matching():
    assert name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[], int)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[], int)"
    )

def test_lenient_matcher_exact_matching_varargs():
    assert name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)"
    )

def test_lenient_matcher_different_parms_varargs():
    assert not name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator()"
    )

def test_lenient_matcher_different_parms():
    assert not name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[])",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator()"
    )

def test_lenient_matcher_simple_arg_types():
    assert name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(CharSequence[])",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[])")

def test_lenient_matcher_simple_arg_types_varargs():
    assert name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)")

def test_lenient_matcher_angle_bracket():
    assert name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.ExtendedMessageFormat.ExtendedMessageFormat(java.lang.String, java.util.Locale, Map<String, ? extends FormatFactory>)",
        "org.apache.commons.lang3.text.ExtendedMessageFormat.ExtendedMessageFormat(java.lang.String, java.util.Locale, java.util.Map<java.lang.String, ? extends org.apache.commons.lang3.text.FormatFactory>)")

def test_lenient_matcher_with_init():
    assert name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupTranslator.<init>(java.lang.CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)"
    )

def test_lenient_matcher_with_diffent_class_init():
    assert not name_utils.lenient_matcher(
        "org.apache.commons.lang3.text.translate.LookupLookupTranslator.<init>(java.lang.CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)"
    )

def test_lenient_matcher_with_simple_name():
    assert name_utils.lenient_matcher(
        "LookupTranslator.LookupTranslator(CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)"
    )

def test_lenient_matcher_with_too_simple_name():
    assert not name_utils.lenient_matcher(
        "LookupTranslator(java.lang.CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)"
    )

def test_lenient_matcher_with_different_pacakge():
    assert not name_utils.lenient_matcher(
        "org.apache.commons.lang.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)"
    )

    assert not name_utils.lenient_matcher(
        "ranslate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)",
        "org.apache.commons.lang3.text.translate.LookupTranslator.LookupTranslator(java.lang.CharSequence[]...)"
    )