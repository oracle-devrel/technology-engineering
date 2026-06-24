"use client";

// Layout components
import V2Row from "./layouts/V2Row";
import V2Col from "./layouts/V2Col";
import V2Grid from "./layouts/V2Grid";
import V2Card from "./layouts/V2Card";
import V2Tabs, { V2Tab } from "./layouts/V2Tabs";
import V2Accordion, { V2Section } from "./layouts/V2Accordion";

// V1 Widget bridge
import V2WidgetAdapter from "./content/V2WidgetAdapter";

// Convenience content (no V1 standalone equivalent)
import V2Text from "./content/V2Text";
import V2Divider from "./content/V2Divider";
import V2Badge from "./content/V2Badge";
import V2Image from "./content/V2Image";
import V2Drawio from "./content/V2Drawio";

// Input components
import V2Form from "./inputs/V2Form";
import V2Input from "./inputs/V2Input";
import V2Select, { V2Option } from "./inputs/V2Select";
import V2Checkbox from "./inputs/V2Checkbox";
import V2Radio from "./inputs/V2Radio";
import V2Toggle from "./inputs/V2Toggle";
import V2Slider from "./inputs/V2Slider";
import V2Date from "./inputs/V2Date";
import V2Time from "./inputs/V2Time";
import V2Rating from "./inputs/V2Rating";
import V2Button from "./inputs/V2Button";
import V2ImageUpload from "./inputs/V2ImageUpload";

function V2Textarea(props) {
  return V2Input({ ...props, attrs: { ...props.attrs, multiline: "true" } });
}

const WIDGET_V2_REGISTRY = {
  // Layout
  row: V2Row,
  col: V2Col,
  grid: V2Grid,
  card: V2Card,
  tabs: V2Tabs,
  tab: V2Tab,
  accordion: V2Accordion,
  section: V2Section,

  // V1 Widget (renders any V1 widget via props)
  widget: V2WidgetAdapter,

  // Convenience content
  text: V2Text,
  divider: V2Divider,
  badge: V2Badge,
  image: V2Image,
  drawio: V2Drawio,

  // Inputs
  form: V2Form,
  input: V2Input,
  textarea: V2Textarea,
  select: V2Select,
  option: V2Option,
  checkbox: V2Checkbox,
  radio: V2Radio,
  toggle: V2Toggle,
  slider: V2Slider,
  date: V2Date,
  time: V2Time,
  rating: V2Rating,
  button: V2Button,
  imageupload: V2ImageUpload,
};

export default WIDGET_V2_REGISTRY;
