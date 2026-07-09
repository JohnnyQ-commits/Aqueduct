"""Unit tests for requirement extraction helpers.

Tests table name extraction, markdown preprocessing, noise filtering.
"""

from __future__ import annotations

from aqueduct.engine.nodes.requirement import (
    _extract_table_names,
    _extract_target_table,
    _is_noise,
    _preprocess_markdown,
)


class TestPreprocessMarkdown:
    def test_unescapes_underscore(self):
        assert _preprocess_markdown(r"dm\_tc\_waybillinfo") == "dm_tc_waybillinfo"

    def test_unescapes_equals(self):
        assert _preprocess_markdown(r"type\=8") == "type=8"

    def test_preserves_plain_text(self):
        assert _preprocess_markdown("plain text") == "plain text"


class TestIsNoise:
    def test_url_fragments(self):
        assert _is_noise("alidocs.oss") is True
        assert _is_noise("zhangjiakou.aliyuncs") is True
        assert _is_noise("resume.png") is True
        assert _is_noise("screenshot.jpg") is True

    def test_real_table_names(self):
        assert _is_noise("dm_tc_waybillinfo.sds_large_aoi") is False
        assert _is_noise("dm_terminal.dw_frontline_staff") is False
        assert _is_noise("my_db.users") is False


class TestExtractTargetTable:
    def test_chinese_label(self):
        text = "目标表：dm_tc_waybillinfo.ads_ecom_di"
        assert _extract_target_table(text) == "dm_tc_waybillinfo.ads_ecom_di"

    def test_create_table(self):
        text = "CREATE TABLE IF NOT EXISTS my_db.target_table (id INT)"
        assert _extract_target_table(text) == "my_db.target_table"

    def test_markdown_escaped_label(self):
        text = r"BDP表：dm\_tc\_waybillinfo.sds\_large\_aoi\_conf"
        assert _extract_target_table(text) == "dm_tc_waybillinfo.sds_large_aoi_conf"

    def test_three_part_name(self):
        text = "some text db_name.schema_name.table_name more text"
        assert _extract_target_table(text) == "db_name.schema_name.table_name"

    def test_url_fragment_filtered(self):
        text = "image from alidocs.oss-cn-zhangjiakou.aliyuncs.com"
        assert _extract_target_table(text) == ""


class TestExtractTableNames:
    def test_extracts_real_tables(self):
        text = r"""
        BDP表：dm\_tc\_waybillinfo.sds\_large\_aoi\_area\_conf\_partitioned
        表：dm\_terminal.dw\_frontline\_staff\_using\_dtl
        表：dm\_next.whl\_ti\_skill\_novice\_train\_stat\_rpt
        """
        names = _extract_table_names(text)
        assert "dm_tc_waybillinfo.sds_large_aoi_area_conf_partitioned" in names
        assert "dm_terminal.dw_frontline_staff_using_dtl" in names
        assert "dm_next.whl_ti_skill_novice_train_stat_rpt" in names

    def test_filters_url_fragments(self):
        text = "https://alidocs.oss-cn-zhangjiakou.aliyuncs.com/resume.png"
        names = _extract_table_names(text)
        # No URL-related names should be extracted
        assert not any("aliyun" in n or "oss" in n or "png" in n for n in names)

    def test_deduplication(self):
        text = "foo.bar appears here and foo.bar appears again"
        names = _extract_table_names(text)
        assert names.count("foo.bar") == 1

    def test_three_part_names_extracted(self):
        text = "db.schema.table is a three-part name"
        names = _extract_table_names(text)
        assert "db.schema.table" in names
