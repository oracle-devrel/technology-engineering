/*!
 * Copyright (c) 2025 Oracle and/or its affiliates.
 * All rights reserved. Oracle Digital Assistant Client Web SDK, Release: 25.02
 */
!(function (e, factory) {
  "object" == typeof exports && "object" == typeof module
    ? (module.exports = factory())
    : "function" == typeof define && define.amd
    ? define("WebSDK", [], factory)
    : "object" == typeof exports
    ? (exports.WebSDK = factory())
    : (e.WebSDK = factory());
  e.WebSDK = factory();
})(self, () =>
  (() => {
    "use strict";
    var e = {
        d: (t, s) => {
          for (var i in s)
            e.o(s, i) &&
              !e.o(t, i) &&
              Object.defineProperty(t, i, { enumerable: !0, get: s[i] });
        },
        o: (e, t) => Object.prototype.hasOwnProperty.call(e, t),
      },
      t = {};
    e.d(t, { default: () => Cc });
    const s = 0,
      i = 1,
      o = 2,
      r = 3,
      a = (e, t) => {
        const s = Math.ceil(t / 2),
          i = e.length / s,
          o = [],
          r = [];
        for (let t = 0; t < e.length; t += i) {
          const s =
            e
              .slice(t, t + i)
              .map((e) => e * e)
              .reduce((e, t) => e + t, 0) / i;
          o.push(s), r.unshift(s);
        }
        return o.splice(0, 1), r.concat(o);
      },
      n = (e, t) => e.map((e) => e * t),
      c = {
        AuthExpiredToken: "AuthExpiredToken",
        AuthNoToken: "AuthNoToken",
        AuthNoChannelId: "AuthNochannelId",
        AuthNoUserId: "AuthNouserId",
        AuthNoExp: "AuthNoexp",
        AuthNoIat: "AuthNoiat",
        AuthInvalidChannelId: "AuthInvalidchannelId",
        AuthInvalidUserId: "AuthInvaliduserId",
        AuthInvalidExp: "AuthInvalidexp",
        AuthInvalidIat: "AuthInvalidiat",
        AuthEmptyChannelIdClaim: "AuthInvalidchannelId",
        AuthEmptyUserIdClaim: "AuthInvaliduserId",
        AuthNegativeExp: "AuthNegativeexp",
        AuthNegativeIat: "AuthNegativeiat",
        AuthExpLessThanIat: "AuthExpLessThanIat",
      };
    class h {
      constructor(e) {
        this.token = e;
        const t = this.token.split(".");
        (this.header = JSON.parse(atob(t[0]))),
          (this.payload = JSON.parse(atob(t[1])));
      }
      getClaim(e) {
        return this.payload[e];
      }
    }
    const l = (e) => "object" == typeof e && null !== e,
      p = (e) => e instanceof Function,
      d = (e) => {
        if (
          !l(e) ||
          ((t = e), ArrayBuffer.isView(t) && !(t instanceof DataView)) ||
          e instanceof ArrayBuffer ||
          e instanceof Event
        )
          return e;
        var t;
        if (e instanceof Blob) return e.slice(0, e.size, e.type);
        if (e instanceof Error) {
          const t = new e.constructor(e.message);
          return (t.stack = e.stack), (t.name = e.name), t;
        }
        return e instanceof Array
          ? e.map((e) => d(e))
          : e instanceof Date
          ? new Date(e)
          : Object.fromEntries(Object.entries(e).map(([e, t]) => [e, d(t)]));
      },
      u = (e) => {
        if (!l(e)) return e;
        for (const t of Object.values(e)) l(t) && u(t);
        return Object.freeze(e);
      },
      g = (e) => {
        const t = {};
        return (
          Object.keys(e).forEach((s) => {
            Object.defineProperty(t, s, {
              get: () => e[s],
              enumerable: !0,
              configurable: !0,
            });
          }),
          t
        );
      },
      m = (e, ...t) => t.reduce((e, t) => t(e), e),
      b = (e) => ((e.lastIndex = 0), e);
    var f = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class w {
      static getInstance() {
        return this.t || (this.t = new w()), this.t;
      }
      get() {
        return f(this, void 0, void 0, function* () {
          if (this.i && y(this.i)) return this.i;
          const e = yield this.l();
          this.i = new h(e);
          try {
            if (
              ((function (e) {
                e || $(c.AuthNoToken);
                const t = "iat",
                  s = e.getClaim(t);
                z(t, x, s);
                const i = e.getClaim(k);
                z(k, x, i), i <= s && $(c.AuthExpLessThanIat);
                const o = "channelId",
                  r = e.getClaim(o);
                z(o, v, r);
                const a = "userId",
                  n = e.getClaim(a);
                z(a, v, n);
              })(this.i),
              y(this.i))
            )
              return this.i;
            throw Error(c.AuthExpiredToken);
          } catch (e) {
            throw e;
          }
        });
      }
      reset() {
        this.i = void 0;
      }
      setFetch(e) {
        if (!p(e))
          throw new Error(
            "'generateAuthToken' is not a function. Create a function that returns a Promise that resolves to a new JWT when called."
          );
        (this.l = e), this.reset();
      }
    }
    const v = "string",
      x = "number",
      k = "exp";
    function y(e) {
      const t = Math.floor((Date.now() + 2e4) / 1e3);
      return e.getClaim(k) > t;
    }
    function z(e, t, s) {
      null == s && $(`AuthNo${e}`),
        typeof s !== t && $(`AuthInvalid${e}`),
        "number" == typeof s
          ? s <= 0 && $(`AuthNegative${e}`)
          : s.length || $(`AuthEmpty${e}`);
    }
    function $(e) {
      throw Error(e);
    }
    class C {
      constructor() {
        (this.promise = new Promise((e, t) => {
          (this.resolve = e), (this.reject = t);
        })),
          Object.freeze(this);
      }
    }
    const S = () => /Android/i.test(navigator.userAgent),
      I = () => /iPhone|iPad/i.test(navigator.userAgent) && !window.MSStream,
      M = (e) => {
        var t;
        const s = document.createElement("div");
        (s.style.display = "none"),
          document.body.appendChild(s),
          (s.innerHTML = e),
          T(s);
        const i = null !== (t = s.textContent) && void 0 !== t ? t : "";
        return s.remove(), i;
      },
      T = (e) => {
        for (let t = e.childElementCount - 1; t >= 0; t--) {
          const s = e.children[t],
            i = window.getComputedStyle(s);
          "none" === i.display || "hidden" === i.visibility ? s.remove() : T(s);
        }
      },
      A = (e) => {
        const t = ((e) => e.replace(/>\s+</g, "><"))(e),
          s = t.replace(/\r\n|\n|\r/g, "<br/>");
        const i = new DOMParser().parseFromString(s, "text/html");
        return null == i ? void 0 : i.body;
      },
      _ = (e) => {
        const t = A(e);
        t.querySelectorAll("script, iframe, link, object, embed, meta").forEach(
          (e) => {
            e.remove();
          }
        );
        return (
          t.querySelectorAll("*").forEach((e) => {
            const t = [];
            for (const s of e.attributes) E(s) && t.push(s);
            for (const s of t) e.removeAttribute(s.name);
          }),
          t.innerHTML
        );
      },
      E = (e) => {
        const t = e.name.toLowerCase(),
          s = e.value.toLowerCase();
        return (
          t.startsWith("on") || "style" === t || s.startsWith("javascript")
        );
      },
      O = (e) => {
        const t = document.createElement("textarea");
        return (t.innerHTML = e), t.value;
      },
      P = (e) => {
        if (!e) return !1;
        const t = window.getComputedStyle(e);
        return (
          !!(
            "none" !== t.display &&
            "hidden" !== t.visibility &&
            "0" !== t.opacity &&
            e.offsetHeight &&
            e.offsetWidth &&
            e.getClientRects().length
          ) && null !== e.offsetParent
        );
      },
      L = (e) => {
        var t;
        return (
          (null !== (t = e.querySelectorAll("button")) && void 0 !== t
            ? t
            : []
          ).forEach((e) => {
            var t, s;
            const i = e.querySelector("a");
            if (i) {
              const s = document.createElement("a");
              return (
                j(i, s),
                (s.innerHTML = i.innerHTML),
                void (
                  null === (t = e.parentElement) ||
                  void 0 === t ||
                  t.replaceChild(s, e)
                )
              );
            }
            const o = document.createElement("div");
            null === (s = e.parentElement) ||
              void 0 === s ||
              s.replaceChild(o, e);
          }),
          e
        );
      },
      j = (e, t) => {
        Array.from(e.attributes).forEach((e) => {
          t.setAttribute(e.name, e.value);
        });
      },
      F = "Enter",
      R = "Escape",
      N = "Space",
      D = "ArrowUp",
      H = "ArrowDown",
      U = "Tab",
      V = "PageDown",
      B = "PageUp",
      W = "Home",
      q = "End",
      Z = "Backspace",
      G = () => {
        const e = new Map();
        return {
          bind: (t, s) => {
            var i;
            t &&
              p(s) &&
              e.set(
                t,
                (null !== (i = e.get(t)) && void 0 !== i ? i : new Set()).add(s)
              );
          },
          trigger: (t, ...s) => {
            const i = e.get(t);
            i &&
              i.forEach((e) => {
                try {
                  e(d(s[0]));
                } catch (e) {
                  console.error(`${String(t)} listener error`, e);
                }
              });
          },
          unbind: (t, s) => {
            if (t)
              if (s) {
                const i = e.get(t);
                i && (i.delete(s), 0 === i.size && e.delete(t));
              } else e.delete(t);
            else e.clear();
          },
        };
      },
      Y = (e, { pattern: t, locale: s }) => {
        const i = new Date(e);
        if ("string" == typeof t)
          try {
            return K(i, t);
          } catch (e) {}
        else if (l(t)) return new Intl.DateTimeFormat(s, t).format(i);
        return X(i, s);
      },
      J = (e, t) => {
        const s = Date.UTC(e.getFullYear(), e.getMonth(), e.getDate()),
          i = Date.UTC(t.getFullYear(), t.getMonth(), t.getDate());
        return Math.floor((i - s) / 864e5);
      },
      K = (e, t) => {
        const s = e.getDate(),
          i = e.getDay(),
          o = ee[i],
          r = e.getMonth() + 1,
          a = te[r - 1],
          n = `${e.getFullYear()}`,
          c = e.getHours(),
          h = e.getMinutes(),
          l = e.getSeconds(),
          p = e.getMilliseconds(),
          d = c >= se ? "PM" : "AM",
          u = ie(e),
          g = c % se || se,
          m = {
            DD: re(s),
            Do: `${s}${oe(s)}`,
            D: `${s}`,
            dddd: o,
            ddd: o.substring(0, 3),
            d: `${i}`,
            MMMM: a,
            MMM: a.substring(0, 3),
            MM: re(r),
            M: `${r}`,
            YYYY: n,
            YY: n.slice(-2),
            HH: re(c),
            H: `${c}`,
            hh: re(g),
            h: `${g}`,
            mm: re(h),
            m: `${h}`,
            ss: re(l),
            s: `${l}`,
            SSS: `${p}`,
            SS: "" + (p % 100),
            S: "" + (p % 1e3),
            A: d,
            a: d.toLowerCase(),
            ZZ: u.replace(":", ""),
            Z: u,
          };
        return t.replace(
          /DD|Do|D|dddd|ddd|d|MMMM|MMM|MM|M|YYYY|YY|HH|H|hh|h|mm|m|ss|s|SSS|SS|S|A|a|ZZ|Z/g,
          (e) => m[e]
        );
      },
      X = (e, t) => {
        const s = null != t ? t : "en";
        return `${e
          .toLocaleDateString(s, {
            weekday: "short",
            month: "short",
            day: "numeric",
          })
          .replace(/,/g, "")}, ${e.toLocaleTimeString(s, {
          hour: "numeric",
          minute: "numeric",
          hour12: !0,
        })}`;
      },
      Q = (e, t, s) => {
        const i = null != s ? s : "en";
        return `${new Intl.RelativeTimeFormat(i, { numeric: "auto" }).format(
          t,
          "day"
        )}, ${e.toLocaleTimeString(i, {
          hour: "numeric",
          minute: "numeric",
          hour12: !0,
        })}`;
      },
      ee = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
      ],
      te = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
      ],
      se = 12,
      ie = (e) => {
        const t = e.getTimezoneOffset(),
          s = Math.abs(t);
        return `${s === t ? "+" : "-"}${re(Math.floor(s / 60))}:${re(s % 60)}`;
      },
      oe = (e) => {
        let t = "th";
        if (e >= 11 && e <= 13) return t;
        switch (e % 10) {
          case 1:
            t = "st";
            break;
          case 2:
            t = "nd";
            break;
          case 3:
            t = "rd";
        }
        return t;
      },
      re = (e) => `${e}`.padStart(2, "0"),
      ae = (e = {}) => {
        if (null === e) return "";
        const {
            prefix: t = "",
            randomPartLength: s = 5,
            separator: i = "-",
            alphanumeric: o = !1,
          } = e,
          r = o ? 36 : 10,
          a = Date.now().toString(r);
        let n = "";
        if (o) n = Math.random().toString(r).replace("0.", "").substring(0, s);
        else {
          const e = Math.pow(10, s);
          n = Math.floor(Math.random() * e)
            .toString(r)
            .padStart(s, "0");
        }
        return `${t}${t ? i : ""}${a}${i}${n}`;
      };
    function ne(e, t, s) {
      return e >= t && e <= s;
    }
    function ce(e) {
      return "number" == typeof e;
    }
    function he(e, t, s) {
      e.addEventListener(t, s);
    }
    function le(e, t, s) {
      e.setRequestHeader(t, s);
    }
    const pe = (e) => "string" == typeof e && e.length > 0,
      de = (e, t, s, i) => me(`${e}${t}${i}`, s),
      ue = (e, t, s = !0, i = "websdk") =>
        de(`ws${s ? "s" : ""}://`, e, t, `/chat/v1/chats/sockets/${i}`),
      ge = (e, t, s = !0) =>
        de(`http${s ? "s" : ""}://`, e, t, "/chat/v1/chats/message"),
      me = (e, t) => {
        const s = Object.keys(t)
          .map((e) => `${e}=${t[e]}`)
          .join("&");
        return s.length ? `${e}?${s}` : e;
      },
      be = (e) => e.replace(/^https?:\/\//i, ""),
      fe = {
        RecognitionNotAvailable: "RecognitionNotAvailable",
        RecognitionNotReady: "RecognitionNotReady",
        RecognitionNoAPI: "RecognitionNoAPI",
        RecognitionProcessingFailure: "RecognitionProcessingFailure",
        RecognitionTooMuchSpeechTimeout: "RecognitionTooMuchSpeechTimeout",
        RecognitionNoResponse: "RecognitionNoResponse",
        RecognitionNoSpeechTimeout: "RecognitionNoSpeechTimeout",
        RecognitionNoWebServer: "RecognitionNoWebServer",
        RecognitionMultipleConnection: "RecognitionMultipleConnection",
      },
      we = {
        DE_DE: "de-de",
        EN_AU: "en-au",
        EN_GB: "en-gb",
        EN_IN: "en-in",
        EN_US: "en-us",
        ES_ES: "es-es",
        FR_FR: "fr-fr",
        HI_IN: "hi-in",
        IT_IT: "it-it",
        PT_BR: "pt-br",
      },
      ve = {
        ASRStart: "asr:start",
        ASRStop: "asr:stop",
        ASRError: "asr:error",
        ASRResponse: "asr:response",
        ASRVisualData: "asr:visualdata",
      },
      xe = Object.keys(we).map((e) => we[e]);
    function ke(e) {
      return xe.includes(e);
    }
    const ye = { TTSStart: "tts:start", TTSStop: "tts:stop" },
      ze = Object.assign(
        Object.assign(
          Object.assign(
            {},
            {
              ConnectionNone: "ConnectionNone",
              ConnectionExplicitClose: "ConnectionExplicitClose",
              MessageInvalid: "MessageInvalid",
              NetworkFailure: "NetworkFailure",
              NetworkOffline: "NetworkOffline",
              ProfileInvalid: "ProfileInvalid",
              TtsNotAvailable: "TtsNotAvailable",
              TTSNoWebAPI: "TTSNoWebAPI",
              SuggestionsEmptyRequest: "SuggestionsEmptyRequest",
              SuggestionsInvalidRequest: "SuggestionsInvalidRequest",
              SuggestionsTimeout: "SuggestionsTimeout",
              UploadBadFile: "UploadBadFile",
              UploadMaxSize: "UploadMaxSize",
              UploadNetworkFail: "UploadNetworkFail",
              UploadNotAvailable: "UploadNotAvailable",
              UploadUnauthorized: "UploadUnauthorized",
              UploadZeroSize: "UploadZeroSize",
              LocationNoAPI: "LocationNoAPI",
              LocationNotAvailable: "LocationNotAvailable",
              LocationTimeout: "LocationTimeout",
              LocationInvalid: "LocationInvalid",
            }
          ),
          c
        ),
        fe
      ),
      $e = {
        Call: "call",
        Client: "client",
        Location: "location",
        Popup: "popup",
        Postback: "postback",
        Share: "share",
        SubmitForm: "submitForm",
        Url: "url",
        Webview: "webview",
      },
      Ce = "primary",
      Se = "danger",
      Ie = "icon",
      Me = "link",
      Te = { Image: "image", Video: "video", Audio: "audio", File: "file" },
      Ae = { Text: "text", Link: "link", Action: "action", Media: "media" },
      _e = Object.assign(Object.assign({}, Ae), {
        SingleSelect: "singleSelect",
        MultiSelect: "multiSelect",
        DatePicker: "datePicker",
        TimePicker: "timePicker",
        Toggle: "toggle",
        TextInput: "textInput",
        NumberInput: "numberInput",
      }),
      Ee = {
        CUSTOM: "custom",
        NAVIGATE: "navigate",
        QUERY: "query",
        UPDATE_FIELDS: "updateFields",
      },
      Oe = {
        Attachment: "attachment",
        Card: "card",
        Location: "location",
        Postback: "postback",
        Raw: "raw",
        Suggest: "suggest",
        Text: "text",
        CloseSession: "closeSession",
        SessionClosed: "sessionClosed",
        Table: "table",
        Form: "form",
        TableForm: "tableForm",
        Status: "status",
        EditForm: "editForm",
        FormSubmission: "formSubmission",
        InboundEvent: "inboundEvent",
        OutboundEvent: "outboundEvent",
        TextStream: "textStream",
        Command: "command",
        Error: "error",
        UpdateApplicationContextCommand: "updateApplicationContextCommand",
        ExecuteApplicationActionCommand: "executeApplicationActionCommand",
        GetDebugInfoCommand: "getDebugInfoCommand",
      },
      Pe = {
        ChatWindow: "chatWindow",
        CompactChat: "compactChat",
        UIWidget: "UIWidget",
        Skill: "skill",
      },
      Le = Object.assign(Object.assign({}, Ee), {
        COPY_MESSAGE_TEXT: "copyMessageText",
      }),
      je = "auth",
      Fe = "ping",
      Re = "pong",
      Ne = "jwt",
      De = { state: { type: Fe } },
      He = "bot",
      Ue = "user",
      Ve = "AGENT",
      Be = "BOT",
      We = (e) => l(e) && "messagePayload" in e,
      qe = (e) => l(e) && "type" in e,
      Ze = (e) => qe(e) && e.type === Oe.Postback,
      Ge = (e) => void 0 !== e.fields,
      Ye = (e) => void 0 !== e.formRows,
      Je = (e) => void 0 !== e.fields,
      Ke = (e) => l(e) && "state" in e;
    function Xe(e, t, s) {
      const i = (function (e) {
        const t = e.split("/")[0].toLowerCase();
        switch (t) {
          case Te.Audio:
          case Te.Image:
          case Te.Video:
            return t;
          default:
            return Te.File;
        }
      })(e);
      return tt({
        type: Oe.Attachment,
        attachment: { type: i, url: t, title: s },
      });
    }
    function Qe(e, t) {
      const s = tt({ text: e, type: Oe.Text });
      return (
        t &&
          (s.sdkMetadata
            ? (s.sdkMetadata.speechId = t)
            : (s.sdkMetadata = { speechId: t })),
        s
      );
    }
    function et(e) {
      var t;
      let s;
      s =
        "label" in e ? e.label : null !== (t = e.text) && void 0 !== t ? t : ot;
      return tt({ text: s, postback: e.postback, type: Oe.Postback });
    }
    function tt(e) {
      return st({ messagePayload: e });
    }
    const st = (e) =>
        e.requestId
          ? e
          : Object.assign(Object.assign({}, e), {
              requestId: ae({ prefix: "wsreq", separator: "/" }),
            }),
      it = "; ",
      ot = "",
      rt = /<[^>]+>/g,
      at = /&#(\d+);/g,
      nt = /&#[xX]([\da-fA-F]+);/g;
    function ct(e, t) {
      const s = e.messagePayload;
      let i = ot;
      if (s.voice)
        return bt(
          (function (e) {
            var t;
            const s = [
              null === (t = e.voice) || void 0 === t ? void 0 : t.text,
            ];
            switch (e.type) {
              case Oe.Card:
                s.push(
                  (function (e) {
                    if (!(null == e ? void 0 : e.length)) return ot;
                    return e
                      .filter((e) => e.voice)
                      .map((e) => {
                        var t;
                        const s = [];
                        return (
                          e.voice &&
                            s.push(
                              null === (t = e.voice) || void 0 === t
                                ? void 0
                                : t.text
                            ),
                          s.push(mt(e.actions)),
                          s.filter(Boolean).join(it)
                        );
                      })
                      .filter(Boolean)
                      .join(it);
                  })(e.cards)
                );
                break;
              case Oe.Form:
              case Oe.TableForm:
                s.push(
                  (function (e) {
                    if (!(null == e ? void 0 : e.length)) return ot;
                    return e
                      .filter(Boolean)
                      .map((e) => e.voice && e.voice.text)
                      .filter(Boolean)
                      .join(it);
                  })(e.forms)
                );
            }
            return (
              s.push(mt(e.actions)),
              s.push(mt(e.globalActions)),
              s.filter(Boolean).join(it)
            );
          })(e.messagePayload)
        );
      switch (s.type) {
        case Oe.Attachment:
          i = (function (e, t) {
            return t[`${e.type}_${e.attachment.type}`];
          })(s, t);
          break;
        case Oe.Card:
          i = (function (e, t) {
            const s = e.cards;
            let i = ot;
            if (null == s ? void 0 : s.length) {
              const e = t.card,
                o = e ? (e.includes("{0}") ? e : `${e} {0}`) : ot,
                r = s.length > 1;
              i = s
                .filter((e) => e.title)
                .map((e, t) => {
                  const s = [r ? o.replace("{0}", `${t + 1}`) : ot];
                  return (
                    e.voice
                      ? s.push(e.voice.text)
                      : (s.push(e.title), s.push(e.description)),
                    s.push(ht(e.actions)),
                    s.filter(Boolean).join(it)
                  );
                })
                .filter(Boolean)
                .join(it);
            }
            return i;
          })(s, t);
          break;
        case Oe.Location:
          i = (function (e) {
            const t = e.location;
            return `${t.title ? `${t.title}${it}` : ot}${t.latitude},${
              t.longitude
            }`;
          })(s);
          break;
        case Oe.Text:
        case Oe.TextStream:
          i = s.text;
          break;
        case Oe.Table:
          i = (function (e, t) {
            return (
              lt(e.paginationInfo) +
              e.rows
                .filter((e) => {
                  var t;
                  return null === (t = null == e ? void 0 : e.fields) ||
                    void 0 === t
                    ? void 0
                    : t.length;
                })
                .map((e, s) => dt(e, s, t))
                .filter(Boolean)
                .join(it)
            );
          })(s, t);
          break;
        case Oe.Form:
          i = (function (e, t) {
            return (
              lt(e.paginationInfo) +
              e.forms
                .filter((e) => e)
                .map((e, s) => {
                  const i = (e.title ? `${e.title}: ` : ot) + pt(e, t);
                  return i
                    ? `${(t.itemIterator || ot).replace(
                        "{0}",
                        `${s + 1}`
                      )}: ${i}`
                    : ot;
                })
                .filter(Boolean)
                .join(it)
            );
          })(s, t);
          break;
        case Oe.TableForm:
          i = (function (e, t) {
            return (
              lt(e.paginationInfo) +
              e.rows
                .filter((e) => {
                  var t;
                  return null === (t = null == e ? void 0 : e.fields) ||
                    void 0 === t
                    ? void 0
                    : t.length;
                })
                .map((s, i) => dt(s, i, t) + it + pt(e.forms[i], t))
                .filter(Boolean)
                .join(it)
            );
          })(s, t);
          break;
        case Oe.EditForm:
          i = (function (e) {
            var t, s;
            return null !==
              (s =
                null !== (t = e.errorMessage) && void 0 !== t ? t : e.title) &&
              void 0 !== s
              ? s
              : ot;
          })(s);
      }
      return m(
        (function (e, t) {
          if (e.type === Oe.EditForm && e.errorMessage) return t;
          const s = [];
          return (
            s.push(e.headerText),
            s.push(t),
            s.push(ht(e.actions)),
            s.push(e.footerText),
            s.push(ht(e.globalActions)),
            s.filter(Boolean).join(it)
          );
        })(s, i),
        bt,
        ft,
        gt
      );
    }
    function ht(e) {
      return e
        ? e
            .filter((e) => e.type !== $e.SubmitForm)
            .map((e) => (e.voice ? e.voice.text : e.label || ot))
            .filter(Boolean)
            .join(it)
        : ot;
    }
    function lt(e) {
      if (e && e.totalCount > e.rangeSize) {
        const t = e.status;
        return t ? t + it : ot;
      }
      return ot;
    }
    function pt(e, t) {
      let s = ht(e.actions);
      return (
        s && (s = it + s),
        Ge(e)
          ? ut(e.fields, t) + s
          : e.formRows
              .filter((e) => (null == e ? void 0 : e.columns.length))
              .map((e) =>
                e.columns
                  .filter((e) => (null == e ? void 0 : e.fields.length))
                  .map((e) => ut(e.fields, t))
                  .filter(Boolean)
                  .join(it)
              )
              .filter(Boolean)
              .join(it) + s
      );
    }
    function dt(e, t, s) {
      return `${(s.itemIterator || ot).replace("{0}", `${t + 1}`)}: ${ut(
        e.fields,
        s
      )}`;
    }
    function ut(e, t) {
      return (null == e ? void 0 : e.length)
        ? e
            .filter((e) => e)
            .map((e) =>
              (function (e, t) {
                var s;
                const i = null !== (s = e.label) && void 0 !== s ? s : ot,
                  o = i ? `${i}: ` : ot;
                switch (e.displayType) {
                  case Ae.Text:
                    return o + (e.value || ot);
                  case Ae.Link:
                    return o + (t.linkField || ot).replace("{0}", i);
                  case Ae.Action:
                    const s = e.action;
                    return o + (s.voice ? s.voice.text : s.label) || ot;
                  default:
                    return i;
                }
              })(e, t)
            )
            .filter(Boolean)
            .join(it)
        : ot;
    }
    function gt(e) {
      if (null == e ? void 0 : e.length) {
        const t = e
          .replace(b(at), (e, t) => String.fromCharCode(t))
          .replace(b(nt), (e, t) => {
            const s = Number.parseInt(`0x${t}`, 16);
            return String.fromCharCode(s);
          });
        return M(t).replace(b(rt), ot);
      }
      return ot;
    }
    function mt(e) {
      return (null == e ? void 0 : e.length)
        ? e
            .filter((e) => e.type !== $e.SubmitForm)
            .map((e) => e.voice && e.voice.text)
            .filter(Boolean)
            .join(it)
        : ot;
    }
    const bt = (e) => e.replaceAll(/([-.,?:;!]);/g, "$1"),
      ft = (e) => e.replaceAll(/\r|\n|<br\/?>/gim, it),
      wt = [
        Oe.Attachment,
        Oe.Card,
        Oe.EditForm,
        Oe.Error,
        Oe.Form,
        Oe.Location,
        Oe.Postback,
        Oe.Raw,
        Oe.Table,
        Oe.TableForm,
        Oe.Text,
        Oe.TextStream,
      ],
      vt = (e) => {
        const t = e.messagePayload.type;
        return wt.includes(t);
      };
    function xt(e) {
      const t = !1;
      if (!We(e)) return t;
      const s = e.messagePayload;
      return qe(s)
        ? (s.actions && !kt(s.actions)) ||
          (s.globalActions && !kt(s.globalActions))
          ? t
          : Boolean(
              (function (e) {
                switch (e.type) {
                  case Oe.Attachment:
                    return (function (e) {
                      const t = e.attachment;
                      return !(!(null == t ? void 0 : t.type) || !t.url);
                    })(e);
                  case Oe.Card:
                    return (function (e) {
                      let t = !1;
                      if (e.layout && e.cards.length) {
                        t = !0;
                        for (const t of e.cards) {
                          if (!t.title) return !1;
                          if (t.actions && !kt(t.actions)) return !1;
                        }
                      }
                      return t;
                    })(e);
                  case Oe.CloseSession:
                  case Oe.SessionClosed:
                    return !0;
                  case Oe.Location:
                    return (function (e) {
                      const t = e.location;
                      return !(
                        !(null == t ? void 0 : t.latitude) || !t.longitude
                      );
                    })(e);
                  case Oe.Postback:
                    return (function (e) {
                      return !!e.postback;
                    })(e);
                  case Oe.Text:
                    return (function (e) {
                      return !!e.text;
                    })(e);
                  case Oe.TextStream:
                    return (function (e) {
                      return "string" == typeof e.text && !!e.streamState;
                    })(e);
                  case Oe.Table:
                    return yt(e);
                  case Oe.Form:
                    return zt(e);
                  case Oe.TableForm:
                    return (function (e) {
                      return yt(e) && zt(e);
                    })(e);
                  case Oe.EditForm:
                    return (function (e) {
                      const t = e.fields,
                        s = e.formColumns,
                        i = e.formRows;
                      return (
                        ((null == t ? void 0 : t.length) > 0 &&
                          t.every((e) =>
                            (function (e) {
                              const t = e.displayType,
                                s = e;
                              return (
                                t &&
                                Object.values(_e).includes(t) &&
                                ((function (e) {
                                  const t = e.id;
                                  let s = !1;
                                  switch (e.displayType) {
                                    case _e.SingleSelect:
                                    case _e.MultiSelect:
                                      s = (function (e) {
                                        const t = e.layoutStyle,
                                          s = e.options;
                                        return (
                                          void 0 !== t &&
                                          "string" == typeof t &&
                                          t.length > 0 &&
                                          void 0 !== s &&
                                          s.length > 0 &&
                                          s.every((e) =>
                                            (function (e) {
                                              const t = e.label,
                                                s = e.value;
                                              return (
                                                void 0 !== t &&
                                                "string" == typeof t &&
                                                t.length > 0 &&
                                                void 0 !== s
                                              );
                                            })(e)
                                          )
                                        );
                                      })(e);
                                      break;
                                    case _e.Toggle:
                                      s = (function (e) {
                                        const t = e.valueOn,
                                          s = e.valueOff;
                                        return (
                                          void 0 !== t &&
                                          "string" == typeof t &&
                                          t.length > 0 &&
                                          void 0 !== s &&
                                          "string" == typeof s &&
                                          s.length > 0
                                        );
                                      })(e);
                                      break;
                                    case _e.DatePicker:
                                    case _e.TimePicker:
                                    case _e.TextInput:
                                    case _e.NumberInput:
                                      s = !0;
                                  }
                                  return s && void 0 !== t && t.length > 0;
                                })(s) ||
                                  Ct(e))
                              );
                            })(e)
                          ) &&
                          "number" == typeof s &&
                          s > 0) ||
                        (null == i ? void 0 : i.length) > 0
                      );
                    })(e);
                  case Oe.FormSubmission:
                    return (function (e) {
                      return !!e.submittedFields;
                    })(e);
                  case Oe.InboundEvent:
                  case Oe.OutboundEvent:
                    return (function (e) {
                      return !!e.eventType && !!e.eventVersion && !!e.eventData;
                    })(e);
                  case Oe.Status:
                    return (function (e) {
                      return e.type === Oe.Status && "status" in e;
                    })(e);
                  case Oe.Command:
                    return (function (e) {
                      return e.type === Oe.Command && "command" in e;
                    })(e);
                  case Oe.UpdateApplicationContextCommand:
                    return (function (e) {
                      const { context: t, source: s } = e;
                      return (
                        void 0 !== t && "string" == typeof t && Mt.includes(s)
                      );
                    })(e);
                  case Oe.GetDebugInfoCommand:
                    return (function (e) {
                      return void 0 !== e.infoTypes && e.infoTypes.length > 0;
                    })(e);
                  case Oe.Error:
                    return Tt(e);
                }
                return !1;
              })(s)
            )
        : t;
    }
    function kt(e) {
      for (const t of e)
        if (
          !t.type ||
          !(
            (t.label && "string" == typeof t.label) ||
            (t.imageUrl && "string" == typeof t.imageUrl)
          )
        )
          return !1;
      return !0;
    }
    function yt(e) {
      const t = e.headings,
        s = e.rows;
      return (
        t &&
        t.length > 0 &&
        s &&
        s.length > 0 &&
        t.every((e) =>
          (function (e) {
            const t = e.label;
            return void 0 !== t && t.length > 0;
          })(e)
        ) &&
        s.every((e) => $t(e))
      );
    }
    function zt(e) {
      const t = e.forms;
      return t && t.length > 0 && t.every((e) => (Ge(e) && $t(e)) || Ye(e));
    }
    function $t(e) {
      const t = e.fields;
      return t && t.length > 0 && t.every((e) => Ct(e));
    }
    function Ct(e) {
      return !!e.displayType && It(e);
    }
    const St = Object.values(Ae);
    function It(e) {
      return e && St.includes(e.displayType);
    }
    const Mt = Object.values(Pe);
    const Tt = (e) => !!e.errorMessage,
      At = (e) =>
        !0 === e || ("string" == typeof e && "true" === e.toLowerCase()),
      _t = Object.assign(
        Object.assign(
          Object.assign(
            Object.assign(
              Object.assign(Object.assign({}, Le), {
                Open: "open",
                Close: "close",
                Error: "error",
                Message: "message",
                MessageReceived: "message:received",
                MessageSent: "message:sent",
                State: "state",
              }),
              Ee
            ),
            ve
          ),
          ye
        ),
        { CoreError: "CoreError" }
      );
    class Et {
      constructor(e) {
        (this.dispatcher = e), (this.state = r);
      }
      getState() {
        return this.state;
      }
      isOpen() {
        return this.state === i;
      }
      isClosed() {
        return this.state === r;
      }
      on(e, t) {
        this.dispatcher.bind(e, t);
      }
      off(e, t) {
        this.dispatcher.unbind(e, t);
      }
      setState(e) {
        (this.state = e), this.dispatcher.trigger(_t.State, e);
      }
    }
    function Ot(e) {
      return Error(e);
    }
    const Pt = navigator,
      Lt = null == Pt ? void 0 : Pt.geolocation,
      jt = 1e5,
      Ft = (e) => Math.round(e * jt) / jt;
    function Rt() {
      return Lt
        ? new Promise((e, t) => {
            Lt.getCurrentPosition(
              (t) => {
                const s = t.coords,
                  i = Object.assign(Object.assign({}, s), {
                    latitude: Ft(s.latitude),
                    longitude: Ft(s.longitude),
                  });
                e(i);
              },
              (e) => {
                let s;
                switch (e.code) {
                  case e.POSITION_UNAVAILABLE:
                    s = ze.LocationNotAvailable;
                    break;
                  case e.TIMEOUT:
                    s = ze.LocationTimeout;
                    break;
                  case e.PERMISSION_DENIED:
                  default:
                    s = ze.LocationNoAPI;
                }
                t(Ot(s));
              },
              { enableHighAccuracy: !0, timeout: 5e3 }
            );
          })
        : ((e = ze.LocationNoAPI), Promise.reject(Ot(e)));
    }
    const Nt = "uae:audiodata",
      Dt = "uae:analyserdata";
    var Ht = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const Ut = () => {
        var e;
        return !!(null === (e = navigator.mediaDevices) || void 0 === e
          ? void 0
          : e.getUserMedia);
      },
      Vt = () =>
        Ht(void 0, void 0, void 0, function* () {
          try {
            const e = yield navigator.mediaDevices.getUserMedia({ audio: !0 }),
              t = new AudioContext();
            return { context: t, streamNode: t.createMediaStreamSource(e) };
          } catch (e) {
            throw Error(fe.RecognitionNoAPI);
          }
        });
    var Bt = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Wt {
      static getInstance() {
        return this.p || (this.p = new Wt()), this.p;
      }
      constructor() {
        (this.u = ((e) => {
          const t = `\nclass VoiceProcessor extends AudioWorkletProcessor {\n    process(inputs) {\n        this.port.postMessage(inputs[0][0]);\n        return true;\n    }\n}\n\nregisterProcessor('${e}', VoiceProcessor);`;
          return URL.createObjectURL(
            new Blob([t], { type: "application/javascript" })
          );
        })(qt)),
          (this.v = !1),
          (this.k = new Float32Array(Yt)),
          (this.$ = 0),
          (this.C = !0),
          (this.I = new Float32Array(0)),
          (this.T = G()),
          (this._ = (e) => {
            this.O && (this.O.resolve(), (this.O = void 0)),
              this.P() && this.L(),
              e.data && this.j(e.data);
          });
      }
      start() {
        return Bt(this, void 0, void 0, function* () {
          if (this.v) return;
          this.v = !0;
          const e = yield Ht(void 0, void 0, void 0, function* () {
            if (!Ut()) throw Error(fe.RecognitionNoAPI);
            return Vt();
          });
          (this.F = e.context), (this.R = e.streamNode);
          const { analyserNode: t, processorNode: s } = yield this.N(e);
          (this.U = t),
            (this.V = s),
            (s.port.onmessage = this._),
            (this.O = new C()),
            yield this.O.promise;
        });
      }
      stop() {
        return Bt(this, void 0, void 0, function* () {
          return this.B();
        });
      }
      getAnalyser() {
        return this.U;
      }
      on(e, t) {
        this.T.bind(e, t);
      }
      N(e) {
        return Bt(this, void 0, void 0, function* () {
          const { context: t, streamNode: s } = e;
          try {
            yield t.audioWorklet.addModule(this.u);
          } catch (e) {
            throw (this.stop(), Error(fe.RecognitionNoWebServer, { cause: e }));
          }
          const i = new AudioWorkletNode(t, qt),
            o = t.createAnalyser();
          return (
            (o.smoothingTimeConstant = Zt),
            (o.fftSize = Gt),
            (this.W = setInterval(() => {
              this.q();
            }, Jt)),
            s.connect(o).connect(i).connect(t.destination),
            { analyserNode: o, processorNode: i }
          );
        });
      }
      P() {
        return this.$ === Yt;
      }
      L() {
        const e = this.$ < Yt ? this.k.slice(0, this.$) : this.k;
        (this.$ = 0), this.G(e);
      }
      j(e) {
        for (const t of e) this.k[this.$++] = t;
      }
      G(e) {
        var t, s;
        const i =
          null !==
            (s =
              null === (t = this.F) || void 0 === t ? void 0 : t.sampleRate) &&
          void 0 !== s
            ? s
            : Kt;
        try {
          const t = this.Y(e, i, Qt);
          this.T.trigger(Nt, t);
        } catch (e) {
          this.stop();
        }
      }
      Y(e, t, s) {
        if (s === t) return e.buffer;
        if (s > t) throw Error();
        let i = [];
        switch (t) {
          case Kt:
            i = es;
            break;
          case Xt:
            i = ts;
            break;
          default:
            throw Error();
        }
        const o = t / s;
        let r, a, n;
        const c = this.C,
          h = this.I;
        c
          ? ((r = Math.floor(e.length % o)),
            (a = e.length - r),
            (n = 0 === r ? Array.from(e) : e.slice(0, a)))
          : ((r = Math.floor((e.length + h.length - i.length) % o)),
            (a = e.length + h.length - i.length - r),
            (n = new Float32Array(h.length + a)),
            n.set(h),
            n.set(e.slice(0, a), h.length));
        const l = Math.floor(a / o),
          p = new Int16Array(l);
        if (t === Kt)
          for (let e = i.length; e < n.length; e += o) {
            let t = 0;
            for (let s = 0; s < i.length; s++) t += n[e - s] * i[s];
            const s = 32767 * Math.max(Math.min(t, 1), -1);
            p[(e - i.length) / o] = s;
          }
        else {
          const e = [];
          for (let t = i.length; t < n.length; t++) {
            let s = 0;
            for (let e = 0; e < i.length; e++) s += n[t - e] * i[e];
            e[t - i.length] = s;
          }
          for (let t = 0; t < l; t++) {
            const s = 3,
              i = t * o,
              r = Math.floor(i) - s + 1,
              a = Math.floor(i) + s;
            let n = 0;
            for (let t = r; t <= a; t++) {
              n +=
                (t < 0 ? e[0] : t >= e.length ? e[e.length - 1] : e[t]) *
                ss(s, i - t);
            }
            p[t] = 32767 * Math.max(Math.min(n, 1), -1);
          }
        }
        return (
          (this.I = c
            ? e.slice(a - i.length - h.length)
            : e.slice(a - i.length - (h.length - i.length))),
          (this.C = !1),
          p.buffer
        );
      }
      q() {
        const e = this.U;
        if (e) {
          const t = new Uint8Array(e.frequencyBinCount);
          e.getByteFrequencyData(t), this.T.trigger(Dt, t);
        }
      }
      B() {
        return Bt(this, void 0, void 0, function* () {
          var e, t, s, i, o, r, a;
          this.v &&
            ((this.v = !1),
            clearInterval(this.W),
            null === (e = this.O) || void 0 === e || e.reject(),
            (this.O = void 0),
            null === (t = this.V) || void 0 === t || t.disconnect(),
            null === (s = this.U) || void 0 === s || s.disconnect(),
            null ===
              (o =
                null === (i = this.R) || void 0 === i
                  ? void 0
                  : i.mediaStream) ||
              void 0 === o ||
              o.getAudioTracks().forEach((e) => {
                e.stop();
              }),
            null === (r = this.R) || void 0 === r || r.disconnect(),
            yield null === (a = this.F) || void 0 === a ? void 0 : a.suspend(),
            (this.V = void 0),
            (this.U = void 0),
            (this.R = void 0),
            (this.C = !0),
            (this.I = new Float32Array(0)),
            (this.k = new Float32Array(Yt)),
            (this.$ = 0));
        });
      }
    }
    const qt = "oda-voice-processor-worklet",
      Zt = 0.8,
      Gt = 256,
      Yt = 4096,
      Jt = 33,
      Kt = 48e3,
      Xt = 44100,
      Qt = 16e3,
      es = [
        -25033838264794034e-21, -3645156113737857e-20, -11489993827892933e-21,
        393243788874656e-19, 6998419352067277e-20, 37556691270439976e-21,
        -476966455345305e-19, -0.00011379935461751734, -8400957697117619e-20,
        4208817777607469e-20, 0.00016391587447478332, 0.00015508372993570357,
        -1253765788919669e-20, -0.00021258262011091092, -0.0002524059896175195,
        -51874329668708116e-21, 0.0002479230009768214, 0.00037351534477673157,
        0.00016157590781788105, -0.0002541085239198603, -0.000510486865332593,
        -0.0003246104617540939, 0.00021219136947965464, 0.0006488877825604561,
        0.0005444416935293036, -0.0001016639071691704, -0.0007673001147209819,
        -0.0008176720912938691, -972696982411551e-19, 0.0008376185852528038,
        0.0011319450250252222, 0.0004008193339799052, -0.0008262743020160207,
        -0.0014643282305934196, -0.0008183365045047033, 0.0006964471772153777,
        0.001780467922489105, 0.0013489288090360295, -0.00041122152287042,
        -0.0020347535966250413, -0.0019782994815083733, -6247794246099269e-20,
        0.002171643809964705, 0.0026761621389245617, 0.00074944268608935,
        -0.00212817775887288, -0.003394541347147186, -0.0016615884301227524,
        0.001837545335885159, 0.004067170702246546, 0.0027936171643976352,
        -0.001233420727213658, -0.004610035314537476, -0.004119319153202972,
        0.00025459137646049936, 0.00492286494534436, 0.005588805700369816,
        0.001150762425755883, -0.004891042781491068, -0.0071267634777626675,
        -0.003021979039818941, 0.00438688631315642, 0.008631467181982988,
        0.005385139236634672, -0.003268406079325266, -0.009973661255235284,
        -0.008256256502745316, 0.0013719935383757782, 0.010993210336541666,
        0.011651337116264694, 0.0015082475865128093, -0.01148872195209017,
        -0.015609515327517686, -0.005671504441670989, 0.011188303272599716,
        0.02024519058502148, 0.011637590928971467, -0.009667754909210324,
        -0.025878090076785515, -0.020500381603699786, 0.006098908137700642,
        0.033428666116203716, 0.03513487017573178, 0.001719739622764723,
        -0.046085580848361105, -0.06623078150315037, -0.023349941728869696,
        0.08292213207159124, 0.21069217442624302, 0.2973829711397418,
        0.2973829711397419, 0.21069217442624305, 0.08292213207159124,
        -0.023349941728869693, -0.06623078150315037, -0.046085580848361105,
        0.0017197396227647225, 0.03513487017573178, 0.033428666116203716,
        0.006098908137700641, -0.020500381603699783, -0.025878090076785508,
        -0.009667754909210326, 0.011637590928971469, 0.020245190585021472,
        0.011188303272599716, -0.00567150444167099, -0.015609515327517682,
        -0.01148872195209017, 0.001508247586512809, 0.011651337116264699,
        0.010993210336541666, 0.0013719935383757782, -0.008256256502745314,
        -0.009973661255235283, -0.0032684060793252657, 0.00538513923663467,
        0.008631467181982988, 0.004386886313156419, -0.0030219790398189413,
        -0.0071267634777626675, -0.0048910427814910715, 0.0011507624257558842,
        0.005588805700369813, 0.00492286494534436, 0.00025459137646049936,
        -0.004119319153202973, -0.004610035314537475, -0.0012334207272136583,
        0.002793617164397636, 0.004067170702246546, 0.0018375453358851592,
        -0.0016615884301227509, -0.0033945413471471847, -0.0021281777588728797,
        0.0007494426860893505, 0.0026761621389245612, 0.0021716438099647056,
        -6247794246099253e-20, -0.001978299481508373, -0.0020347535966250404,
        -0.00041122152287042, 0.0013489288090360292, 0.0017804679224891048,
        0.0006964471772153777, -0.0008183365045047026, -0.00146432823059342,
        -0.0008262743020160207, 0.0004008193339799063, 0.0011319450250252222,
        0.0008376185852528037, -9726969824115494e-20, -0.0008176720912938694,
        -0.0007673001147209783, -0.00010166390716916983, 0.0005444416935293033,
        0.0006488877825604562, 0.0002121913694796546, -0.00032461046175409424,
        -0.000510486865332593, -0.00025410852391986036, 0.0001615759078178811,
        0.0003735153447767315, 0.00024792300097682137, -5187432966870808e-20,
        -0.0002524059896175194, -0.00021258262011091095, -1253765788919669e-20,
        0.0001550837299357036, 0.0001639158744747833, 42088177776074685e-21,
        -8400957697117623e-20, -0.00011379935461751733, -4769664553453051e-20,
        3755669127044002e-20, 699841935206728e-19, 393243788874656e-19,
        -11489993827892933e-21, -3645156113737856e-20, -2503383826479402e-20,
      ],
      ts = [
        -5044267067893139e-21, 5738740247594612e-21, 1611195555688156e-20,
        10560179594562795e-21, -1242816862904201e-20, -3084430704328611e-20,
        -18160396924882423e-21, 2303124169528074e-20, 5216612702894834e-20,
        2806026886746509e-20, -389608521587068e-19, -8174245278012476e-20,
        -4037543061985353e-20, 619375276294956e-19, 0.00012143092661620545,
        55083199655424166e-21, -9401891583478883e-20, -0.00017326981522755043,
        -7198069055926206e-20, 0.0001376274218691789, 0.00023946132645647525,
        9064030545698025e-20, -0.00019557611633250834, -0.0003223511502826996,
        -0.00011036322783022617, 0.0002710935667931249, 0.00042440564349633953,
        0.00013013140955365376, -0.00036784896615780913, -0.0005481886438481025,
        -0.00014855826094166272, 0.0004899798946967381, 0.000696340560985472,
        0.00016383778624615643, -0.0006421263408051642, -0.0008715631880363658,
        -0.00017369118859371453, 0.000829476349448821, 0.0010766146787146871,
        0.00017530890385814463, -0.0010578310750603923, -0.001314320458073489,
        -0.0001652844648711556, 0.0013337004262191077, 0.0015876076783199174,
        0.000139534308084411, -0.0016644454627712116, -0.001899573527380014,
        -9319422024995832e-20, 0.002058491185395933, 0.0022536018141979036,
        20477911370491685e-21, -0.0025256449668619525, -0.0026535487754524955,
        8552498376473957e-20, 0.0030775744811722015, 0.0031040297261921,
        -0.00023314744969763122, -0.003728529808331677, -0.003610856230113392,
        0.000432598472497653, 0.0044964472481822506, 0.004181705019767344,
        -0.0006966685466235378, -0.005404666489478738, -0.00482715710731867,
        0.0010418556659416306, 0.006484667519607787, 0.00556235368742558,
        -0.0014902159613265254, -0.007780573986407925, -0.0064097301786953595,
        0.002072517010858728, 0.009356870546119134, 0.0074037416266333166,
        -0.00283386009764953, -0.011312323822665827, -0.008599512596140524,
        0.003844300507349054, 0.013806774337071994, 0.01008985372973804,
        -0.005220460312862638, -0.01711716324115331, -0.01204196749753927,
        0.007174046245357611, 0.021768247992024713, 0.01478690833035584,
        -0.010136389804721707, -0.02888735624896028, -0.019078400739739057,
        0.015146805312378952, 0.041410446665863104, 0.027068163980255515,
        -0.025512027260482153, -0.07011218378743589, -0.04829678433503421,
        0.06041368701604651, 0.21199607414538668, 0.3213532652447261,
        0.3213532652447261, 0.21199607414538668, 0.060413687016046526,
        -0.04829678433503422, -0.07011218378743589, -0.025512027260482153,
        0.027068163980255515, 0.041410446665863104, 0.015146805312378952,
        -0.019078400739739057, -0.02888735624896028, -0.010136389804721703,
        0.01478690833035584, 0.021768247992024713, 0.007174046245357611,
        -0.01204196749753927, -0.01711716324115331, -0.005220460312862639,
        0.010089853729738038, 0.013806774337071994, 0.0038443005073490553,
        -0.008599512596140524, -0.011312323822665827, -0.0028338600976495314,
        0.007403741626633317, 0.009356870546119134, 0.002072517010858727,
        -0.006409730178695359, -0.007780573986407925, -0.001490215961326526,
        0.005562353687425577, 0.006484667519607787, 0.0010418556659416256,
        -0.004827157107318673, -0.005404666489478739, -0.0006966685466235378,
        0.004181705019767345, 0.004496447248182251, 0.0004325984724976533,
        -0.003610856230113392, -0.003728529808331677, -0.0002331474496976315,
        0.0031040297261921003, 0.003077574481172201, 8552498376473897e-20,
        -0.002653548775452496, -0.002525644966861952, 2047791137049164e-20,
        0.002253601814197904, 0.002058491185395933, -9319422024995909e-20,
        -0.001899573527380014, -0.0016644454627712118, 0.00013953430808441038,
        0.0015876076783199174, 0.0013337004262191077, -0.0001652844648711556,
        -0.0013143204580734896, -0.0010578310750603925, 0.00017530890385814333,
        0.0010766146787146878, 0.0008294763494488195, -0.00017369118859371463,
        -0.00087156318803637, -0.0006421263408051633, 0.00016383778624615698,
        0.0006963405609854716, 0.0004899798946967381, -0.00014855826094166245,
        -0.0005481886438481027, -0.00036784896615780924, 0.00013013140955365368,
        0.00042440564349633964, 0.00027109356679312505, -0.00011036322783022619,
        -0.0003223511502826996, -0.00019557611633250842, 9064030545698017e-20,
        0.00023946132645647525, 0.00013762742186917883, -7198069055926207e-20,
        -0.0001732698152275505, -9401891583478886e-20, 5508319965542416e-20,
        0.00012143092661620549, 6193752762949557e-20, -4037543061985352e-20,
        -8174245278012477e-20, -38960852158706805e-21, 28060268867465078e-21,
        52166127028948336e-21, 2303124169528077e-20, -18160396924882423e-21,
        -30844307043286126e-21, -12428168629042018e-21, 10560179594562806e-21,
        1611195555688157e-20, 5738740247594605e-21, -5044267067893138e-21,
      ],
      ss = (e, t) => {
        let s;
        if (0 === t) s = 1;
        else if (Math.abs(t) >= e) s = 0;
        else {
          const i = Math.PI * t;
          s = (e * Math.sin(i) * Math.sin(i / e)) / Math.pow(i, 2);
        }
        return s;
      };
    var is = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class os {
      static getInstance() {
        return this.t || (this.t = new os()), this.t;
      }
      constructor() {
        (this.J = Wt.getInstance()),
          (this.v = !1),
          (this.K = []),
          (this.X = (e) => {
            try {
              this.ee(e);
            } catch (e) {
              this.te(fe.RecognitionProcessingFailure), this.se();
            }
          }),
          (this.ie = (e) => {
            var t;
            null === (t = this.oe) ||
              void 0 === t ||
              t.trigger(ve.ASRVisualData, e);
          }),
          (this.re = () =>
            is(this, void 0, void 0, function* () {
              var e;
              if (this.ae.tokenGenerator) {
                const t = yield this.ne.get();
                null === (e = this.ce) ||
                  void 0 === e ||
                  e.send(`Bearer ${t.token}`);
              }
              this.he();
            })),
          (this.le = () => {
            this.v && this.se();
          }),
          (this.pe = (e) => {
            try {
              const t = JSON.parse(e.data);
              if (!t.event && t.code) return;
              const s = (function (e) {
                let t, s;
                const i = e.requestId,
                  o = e.nbest;
                "partialResult" === e.event
                  ? ((t = "partial"), (s = o[0].utterance))
                  : (null == o ? void 0 : o.length)
                  ? ((t = "final"), (s = o[0].utterance))
                  : ((t = "error"),
                    (s = e.resultCode
                      ? fe.RecognitionTooMuchSpeechTimeout
                      : fe.RecognitionNoSpeechTimeout));
                return { requestId: i, type: t, text: s, message: e };
              })(t);
              this.ue(s);
            } catch (e) {
              this.te(fe.RecognitionProcessingFailure), this.se();
            }
          }),
          (this.ge = () => {
            var e;
            this.me() &&
              (this.te(fe.RecognitionProcessingFailure),
              null === (e = this.ce) || void 0 === e || e.close());
          }),
          this.J.on(Dt, this.ie),
          this.J.on(Nt, this.X);
      }
      startRecognition() {
        return is(this, void 0, void 0, function* () {
          var e;
          if (!this.v) {
            if (((this.v = !0), this.ce)) {
              const e = this.ce.readyState;
              if (e === o || e === s) return;
            }
            try {
              yield this.J.start(),
                null === (e = this.oe) ||
                  void 0 === e ||
                  e.trigger(ve.ASRStart),
                this.be || (yield this.fe()),
                (this.ce = this.we(this.be));
            } catch (e) {
              throw (this.B(), e);
            }
          }
        });
      }
      stopRecognition() {
        return is(this, void 0, void 0, function* () {
          return this.B();
        });
      }
      setConfig(e) {
        return is(this, void 0, void 0, function* () {
          return (
            e.recognitionLocale || (e.recognitionLocale = we.EN_US),
            e.tokenGenerator && (this.ne = w.getInstance()),
            (this.ae = e),
            (this.oe = e.dispatcher),
            this.fe()
          );
        });
      }
      setLocale(e) {
        ke(e) &&
          this.ae &&
          ((this.ae.recognitionLocale = e),
          this.fe().catch((e) => {
            console.warn(
              "[WebSDK][RecognitionService] - Failed to get server URL",
              e
            );
          }));
      }
      ee(e) {
        var t;
        this.me() && !this.K.length
          ? null === (t = this.ce) || void 0 === t || t.send(e)
          : this.K.push(e);
      }
      ue(e) {
        var t;
        null === (t = this.oe) || void 0 === t || t.trigger(ve.ASRResponse, e),
          ["final", "error"].includes(e.type) && this.se();
      }
      fe() {
        return is(this, void 0, void 0, function* () {
          this.be = yield rs(this.ae, this.ne);
        });
      }
      we(e) {
        var t;
        try {
          const t = new WebSocket(e);
          return (
            (t.onopen = this.re),
            (t.onclose = this.le),
            (t.onmessage = this.pe),
            (t.onerror = this.ge),
            t
          );
        } catch (e) {
          const s = new Error(fe.RecognitionNotReady);
          throw (
            (null === (t = this.oe) ||
              void 0 === t ||
              t.trigger(ve.ASRError, s),
            s)
          );
        }
      }
      te(e) {
        var t;
        null === (t = this.oe) ||
          void 0 === t ||
          t.trigger(ve.ASRResponse, { requestId: "", text: e, type: "error" });
      }
      he() {
        var e;
        if (this.me())
          for (; this.K.length; ) {
            const t = this.K.shift();
            t && (null === (e = this.ce) || void 0 === e || e.send(t));
          }
      }
      me() {
        var e;
        return (
          (null === (e = this.ce) || void 0 === e ? void 0 : e.readyState) === i
        );
      }
      se() {
        this.B().catch((e) => {
          console.warn("[WebSDK][EndRecognition]", e);
        });
      }
      B() {
        return is(this, void 0, void 0, function* () {
          var e;
          if (!this.v) return;
          this.v = !1;
          const t = this.ce;
          this.me() && (null == t || t.send("Done")),
            null == t || t.close(),
            (this.ce = void 0),
            (this.K = []),
            yield this.J.stop(),
            null === (e = this.oe) || void 0 === e || e.trigger(ve.ASRStop);
        });
      }
    }
    const rs = (e, t) =>
        is(void 0, void 0, void 0, function* () {
          if (e.tokenGenerator) {
            const s = yield t.get();
            (e.channelId = s.getClaim("channelId")),
              (e.userId = s.getClaim("userId"));
          }
          if (!e.channelId || !e.userId) throw Error(fe.RecognitionNotReady);
          return (function (e) {
            const { channelId: t, userId: s, tokenGenerator: i, URI: o } = e,
              r = `ws${e.isTLS ? "s" : ""}://`,
              a = `${as}/${e.recognitionLocale}/${ns}`,
              n = Object.assign(
                { channelId: t, userId: s, encodeURI: "audio/raw" },
                i && { jwtInBody: "true" }
              );
            return de(r, o, n, a);
          })(e);
        }),
      as = "/voice/stream/recognize",
      ns = "generic";
    var cs = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    let hs = 1,
      ls = 1,
      ps = 1;
    const ds = window,
      us = ds.addEventListener,
      gs = ds.speechSynthesis,
      ms = ds.SpeechSynthesisUtterance,
      bs = ds.navigator,
      fs = clearTimeout;
    class ws {
      constructor() {
        if (((this.v = !1), (this.oe = G()), !ds || !gs || !ms))
          throw Error("TTSNoWebAPI");
        zs()
          .then((e) => {
            this.ve = e;
          })
          .catch(() => {
            this.ve = void 0;
          }),
          us("beforeunload", (e) => {
            gs.cancel(), fs(this.xe), delete e.returnValue;
          }),
          us(
            "click",
            () => {
              gs && (gs.cancel(), gs.resume(), gs.speak(new ms(" ")));
            },
            { once: !0 }
          );
      }
      setConfig(e) {
        return Promise.resolve();
      }
      speak(e) {
        if (this.ve) {
          const t = new ms(e);
          (t.voice = this.ve),
            (t.pitch = hs),
            (t.rate = ls),
            (t.volume = ps),
            gs.paused && gs.resume(),
            this.v || ((this.v = !0), this.oe.trigger(ye.TTSStart)),
            gs.speak(t),
            this.ve.localService || (fs(this.xe), Cs((e) => (this.xe = e)));
        }
      }
      cancel() {
        gs.speaking && (gs.cancel(), fs(this.xe));
      }
      getVoices() {
        return cs(this, void 0, void 0, function* () {
          return vs();
        });
      }
      setVoice(e) {
        return cs(this, void 0, void 0, function* () {
          return (function (e) {
            const t = e.map((e) => Object.assign({ lang: "", name: "" }, e));
            return vs().then((e) => {
              for (const s of t)
                for (const t of e)
                  if (Ss(s.lang, t.lang) && Ss(s.name, t.name)) return t;
              for (const s of t)
                for (const t of e) if (Ss(s.lang, t.lang)) return t;
              for (const s of t)
                for (const t of e) if (t.lang.includes(s.lang)) return t;
              return zs();
            });
          })(e).then((e) => {
            var t, s, i;
            (this.ve = e),
              (hs = null !== (t = e.pitch) && void 0 !== t ? t : 1),
              (ls = null !== (s = e.rate) && void 0 !== s ? s : 1),
              (ps = null !== (i = e.volume) && void 0 !== i ? i : 1);
          });
        });
      }
      getVoice() {
        return this.ve;
      }
      on(e, t) {
        this.oe.bind(e, t);
      }
      off(e, t) {
        this.oe.unbind(e, t);
      }
    }
    function vs() {
      return new Promise((e) => {
        xs(e),
          gs.addEventListener("voiceschanged", () => {
            xs(e);
          });
      });
    }
    function xs(e) {
      const t = gs.getVoices();
      if (t.length) {
        e(
          (function (e) {
            if (!Array.isArray(e)) return e.ke;
            return e;
          })(ys(t))
        );
      }
    }
    const ks = [
        "Albert",
        "Bad News",
        "Bahh",
        "Bells",
        "Boing",
        "Bubbles",
        "Cellos",
        "Good News",
        "Jester",
        "Organ",
        "Superstar",
        "Trinoids",
        "Whisper",
        "Wobble",
        "Zarvox",
      ],
      ys = (e) => e.filter((e) => !ks.includes(e.name));
    function zs() {
      return vs().then((e) => {
        let t;
        const s = e.filter((e) => e.default);
        if ((1 === s.length && (t = s[0]), !t)) {
          const s = null == bs ? void 0 : bs.language;
          s && (t = e.find((e) => Ss(e.lang, s)));
        }
        if (!t) {
          const s = null == bs ? void 0 : bs.language.substring(0, 2);
          s && (t = e.find((e) => Is(e.lang).includes(s)));
        }
        return t || (t = e[0]), t;
      });
    }
    const $s = 1e4;
    function Cs(e) {
      const t = setTimeout(() => {
        gs.speaking && (gs.pause(), gs.resume(), Cs(e));
      }, $s);
      e(t);
    }
    function Ss(e, t) {
      return Is(e) === Is(t);
    }
    const Is = (e) => e.toLowerCase();
    var Ms = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const Ts = "ended",
      As = "suspended";
    const _s = (e, t) => new Float32Array([...e, ...Es(t)]),
      Es = (e) => Float32Array.from(new Int16Array(e), (e) => e / 32768);
    var Os = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const Ps = "speak",
      Ls = "channelId",
      js = "userId",
      Fs = /<[\w]+/g,
      Rs = Ps;
    class Ns {
      constructor(e) {
        (this.ye = ""),
          (this.ze = []),
          (this.$e = !1),
          (this.v = !1),
          (this.Ce = new AbortController()),
          (this.oe = G()),
          (this.ae = (e) => {
            (this.Se = e),
              (this.ye = `${e.URI}/tts/`),
              e.tokenGenerator && (this.ne = w.getInstance());
          }),
          (this.Ie = (e) =>
            Os(this, void 0, void 0, function* () {
              let t = e;
              e.match(Fs) && (t = `<${Rs}>${e}</${Rs}>`);
              const s = Object.assign(
                  { text: encodeURIComponent(t), stream: "chunked" },
                  this.ve && { voice: this.ve.name }
                ),
                i = yield this.Me(Ps, s);
              return this.Te(i);
            })),
          (this.Me = (e, ...t) =>
            Os(this, [e, ...t], void 0, function* (e, t = {}) {
              const s = this.Se;
              if (s)
                if (s.tokenGenerator) {
                  const e = yield this.ne.get();
                  (t[Ls] = e.getClaim(Ls)), (t[js] = e.getClaim(js));
                } else (t[Ls] = s.channelId), (t[js] = s.userId);
              return de("https://", this.ye, t, e);
            })),
          (this.Te = (e, ...t) =>
            Os(this, [e, ...t], void 0, function* (e, t = !0) {
              var s;
              const i = t ? this.Ce.signal : void 0,
                o = {};
              if (
                null === (s = this.Se) || void 0 === s
                  ? void 0
                  : s.tokenGenerator
              ) {
                const e = yield this.ne.get();
                o.Authorization = `Bearer ${e.token}`;
              }
              return fetch(e, { signal: i, headers: o });
            })),
          (this.Ae = (e) => {
            if (null == e ? void 0 : e.body) {
              const t = e.body.getReader();
              this._e(),
                this.v || ((this.v = !0), this.oe.trigger(ye.TTSStart)),
                this.Ee(t);
            }
          }),
          (this.Ee = (e) =>
            Os(this, void 0, void 0, function* () {
              try {
                const { done: t, value: s } = yield e.read();
                if (t) return void this.Oe.next();
                let i = s.buffer;
                if (
                  (this.$e ||
                    ((this.$e = !0), this.Pe.config(Vs(i)), (i = Us(i))),
                  void 0 !== this.Le)
                ) {
                  const e = new Uint8Array(i),
                    t = new Uint8Array(e.length + 1);
                  (t[0] = this.Le),
                    t.set(e, 1),
                    (i = Hs(t)),
                    (this.Le = void 0);
                }
                if (i.byteLength % 2) {
                  const e = new Uint8Array(i),
                    t = new Uint8Array(e.length - 1);
                  t.set(e.slice(0, e.length - 1)),
                    (i = Hs(t)),
                    (this.Le = e[e.length - 1]);
                }
                this.Pe.play(i), this.Ee(e);
              } catch (e) {
                this.Oe.next();
              }
            })),
          (this._e = () => {
            (this.$e = !1), (this.Le = void 0);
          }),
          (this.je = () => {
            this.v && ((this.v = !1), this.oe.trigger(ye.TTSStop));
          }),
          (this.Fe = () =>
            Os(this, void 0, void 0, function* () {
              const e = yield this.getVoices();
              this.ve = e.find((e) => e.default);
            })),
          this.ae(e),
          (this.Oe = Ds(this.Ae, () => {})),
          (this.Pe = (function (e) {
            let t,
              s,
              i,
              o = e,
              r = [],
              a = () => {},
              n = 0,
              c = !0;
            const h = () =>
                Ms(this, void 0, void 0, function* () {
                  t || (t = new AudioContext()),
                    t.state === As && (yield t.resume());
                }),
              l = () => {
                r.forEach((e) => {
                  e.removeEventListener(Ts, u), e.stop(), e.disconnect();
                }),
                  (r = []);
              },
              p = () =>
                Ms(this, void 0, void 0, function* () {
                  (null == t ? void 0 : t.state) !== As &&
                    (yield null == t ? void 0 : t.suspend()),
                    (i = new Float32Array()),
                    (c = !0),
                    (n = 0),
                    (r = []);
                }),
              d = () => {
                if (!t || !i.length) return;
                if (c && i.length < 4096) return void (c = !1);
                c = !1;
                const e = i.length,
                  a = new AudioBuffer({ sampleRate: o.sampleRate, length: e });
                for (let t = 0; t < o.numChannels; t++) {
                  const s = a.getChannelData(t);
                  for (let t = 0; t < e; t++) s[t] = i[t];
                }
                n < t.currentTime && (n = t.currentTime),
                  s && s.removeEventListener(Ts, u),
                  (s = new AudioBufferSourceNode(t, { buffer: a })),
                  s.connect(t.destination),
                  s.addEventListener(Ts, u),
                  s.start(n),
                  (n += a.duration),
                  r.push(s),
                  (i = new Float32Array());
              },
              u = () => {
                (n = 0),
                  setTimeout(() => {
                    n || (p().catch(() => {}), a());
                  }, 250);
              };
            return (
              (() => {
                const e = document.body,
                  s = ["touchend", "click"];
                let i = !0,
                  o = 0;
                const r = () => {
                    i &&
                      ((t = new AudioContext()),
                      "closed" !== t.state &&
                        t
                          .resume()
                          .then(() => {
                            a(), (o = 0);
                          })
                          .catch((e) => {
                            o++, o < 3 ? r() : console.error(e);
                          }));
                  },
                  a = () => {
                    s.forEach((t) => {
                      e.removeEventListener(t, r);
                    }),
                      (i = !1);
                  };
                s.forEach((t) => {
                  e.addEventListener(t, r);
                });
              })(),
              {
                play: (e) =>
                  Ms(this, void 0, void 0, function* () {
                    (i = i ? _s(i, e) : Es(e)), yield h(), d();
                  }),
                stop: () =>
                  Ms(this, void 0, void 0, function* () {
                    t && (l(), yield p(), a());
                  }),
                config: (e) => {
                  o = Object.assign(Object.assign({}, o), e);
                },
                onEnd: (e) => {
                  a = e;
                },
              }
            );
          })({ sampleRate: 22050, numChannels: 1 })),
          this.Pe.onEnd(this.je),
          this.Fe().catch(() => {}),
          window.addEventListener("beforeunload", () => {
            this.cancel();
          });
      }
      setConfig(e) {
        return Os(this, void 0, void 0, function* () {
          this.ae(e), (this.ze = []), yield this.Fe();
        });
      }
      speak(e) {
        "string" == typeof e && e.trim().length && this.Oe.push(this.Ie(e));
      }
      cancel() {
        this.Ce.abort(),
          (this.Ce = new AbortController()),
          this.Oe.cancel(),
          this.v && this.Pe.stop().catch(() => {});
      }
      getVoices() {
        return Os(this, void 0, void 0, function* () {
          let e = this.ze;
          if (e.length) return e;
          if (this.Re) return this.Re;
          return (
            (this.Re = this.Me("voices")
              .then((t) =>
                Os(this, void 0, void 0, function* () {
                  try {
                    const s =
                      (yield (yield this.Te(t, !1)).json()).voices || [];
                    return (
                      (e = s.map((e) => ({
                        name: e.name,
                        lang: Bs(e.culture),
                        default: !!e.default,
                      }))),
                      (this.ze = e),
                      e
                    );
                  } catch (t) {
                    return e;
                  }
                })
              )
              .catch(() => e)),
            setTimeout(() => {
              this.Re = void 0;
            }),
            this.Re
          );
        });
      }
      getVoice() {
        return this.ve;
      }
      setVoice(e) {
        return Os(this, void 0, void 0, function* () {
          if (!e || !Array.isArray(e) || !e.length)
            throw Error("TTSEmptyParam");
          if (
            this.ve &&
            1 === e.length &&
            !e[0].name &&
            Bs(e[0].lang) === this.ve.lang
          )
            return;
          const t = yield this.getVoices();
          if (!t.length) throw Error("TTSNoVoices");
          if (
            !e.find((e) => {
              var s;
              let i,
                o = !1;
              if (e.name) {
                const s = Bs(e.name);
                i = t.find((e) => s === Bs(e.name));
              }
              if (!i && e.lang) {
                const o = Bs(e.lang);
                let r = t.filter((e) => o === e.lang);
                r.length || (r = t.filter((e) => o === e.lang.split("-")[0])),
                  (i =
                    null !== (s = r.find((e) => e.default)) && void 0 !== s
                      ? s
                      : r[0]);
              }
              return i && ((this.ve = i), (o = !0)), o;
            })
          )
            throw Error("TTSNoMatch");
        });
      }
      on(e, t) {
        this.oe.bind(e, t);
      }
      off(e, t) {
        this.oe.unbind(e, t);
      }
    }
    const Ds = (e, t) => {
        const s = [],
          i = () => {
            s.length && s[0].then(e).catch(t);
          };
        return {
          push: (e) => {
            e.catch(() => {
              const t = s.indexOf(e);
              t > 0 && s.splice(t, 1);
            }),
              s.push(e),
              1 === s.length && i();
          },
          cancel: () => {
            s.length = 0;
          },
          next: () => {
            s.shift(), i();
          },
        };
      },
      Hs = (e) => e.buffer.slice(e.byteOffset, e.byteLength + e.byteOffset),
      Us = (e) => {
        const t = new Uint8Array(e),
          s = new Uint8Array(t.length - 44);
        return s.set(t.slice(44, t.length)), Hs(s);
      },
      Vs = (e) => {
        const t = new DataView(e, 0, 44),
          s = !0;
        return {
          numChannels: t.getUint16(22, s),
          sampleRate: t.getUint32(24, s),
        };
      },
      Bs = (e) => e.toLowerCase();
    var Ws = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const qs = "/chat/v1/attachments",
      Zs = "channelId",
      Gs = "userId";
    class Ys {
      static getInstance() {
        return this.t || (this.t = new Ys()), this.t;
      }
      setConfig(e) {
        return Ws(this, void 0, void 0, function* () {
          if (((this.Se = e), e.tokenGenerator)) {
            this.ne = w.getInstance();
            const t = yield this.ne.get();
            (e[Zs] = t.getClaim(Zs)), (e[Gs] = t.getClaim(Gs));
          }
          this.Ne = (function (e) {
            const t = `http${e.isTLS ? "s" : ""}://`,
              { URI: s, channelId: i, userId: o } = e;
            return de(t, s, { channelId: i, userId: o }, qs);
          })(e);
        });
      }
      upload(e, t) {
        return Ws(this, void 0, void 0, function* () {
          if (!this.Ne) throw Error(ze.UploadNotAvailable);
          const s = e.size;
          if (0 === s) throw Error(ze.UploadZeroSize);
          if (s > 26214400) throw Error(ze.UploadMaxSize);
          const i = new XMLHttpRequest(),
            o = new Promise((e, t) => {
              const s = () => t(Error(ze.UploadNetworkFail));
              he(i, "readystatechange", () => {
                if (4 === i.readyState)
                  switch (i.status) {
                    case 200: {
                      const t = JSON.parse(i.responseText);
                      e(t);
                      break;
                    }
                    case 413:
                      t(Error(ze.UploadMaxSize));
                      break;
                    case 415:
                      t(Error(ze.UploadBadFile));
                      break;
                    default:
                      s();
                  }
              }),
                he(i, "abort", s),
                he(i, "error", s),
                he(i, "timeout", s);
            }),
            r = { file: e, options: t };
          if (this.Se.tokenGenerator) {
            const e = yield this.ne.get();
            r.token = e.token;
          }
          return this.De(i, r), o;
        });
      }
      De(e, { file: t, options: s, token: i }) {
        const o = new FormData();
        o.append("attachment", t, encodeURI(t.name)),
          e.open("POST", this.Ne),
          le(e, "x-oda-meta-file-size", t.size.toString()),
          i &&
            (le(e, "Authorization", `Bearer ${i}`),
            this.Se.enableAttachmentSecurity &&
              (le(e, "x-oda-meta-file-isProtected", "True"),
              le(e, "x-oda-meta-file-authType", "ChannelClientAuth"))),
          e.send(o),
          (null == s ? void 0 : s.onInitUpload) && s.onInitUpload(e);
      }
    }
    const Js = {
      AUDIO: ".aac, .amr, .m4a, .mp3, .mp4a, .mpga, .oga, .ogg, .wav, audio/*",
      FILE: ".7z, .csv, .doc, .docx, .eml, .ics, .key, .log, .msg, .neon, .numbers, .odt, .pages, .pdf, .pps, .ppsx, .ppt, .pptx, .rtf, .txt, .vcf, .xls, .xlsx, .xml, .yml, .yaml, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      IMAGE:
        ".gif, .jfif, .jpeg, .jpg, .png, .svg, .tif, .tiff, .webp, image/*",
      VIDEO:
        ".3g2, .3gp, .avi, .m4v, .mov, .mp4, .mpeg, .mpg, .ogv, .qt, .webm, .wmv, video/*",
      ALL: "",
    };
    Js.ALL = `${Js.AUDIO},${Js.FILE},${Js.IMAGE},${Js.VIDEO}`;
    var Ks = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Xs extends Et {
      constructor(e) {
        super(e.dispatcher),
          (this.He = null),
          (this.Ue = null),
          (this.Ve = 0),
          (this.url = e.url),
          (this.authService = e.authService);
      }
      open() {
        return Ks(this, void 0, void 0, function* () {
          if (!this.isOpen()) {
            if (navigator.onLine) return this.Be();
            throw Error(ze.NetworkOffline);
          }
        });
      }
      close() {
        return Ks(this, void 0, void 0, function* () {
          if (!this.isClosed()) return this.We();
        });
      }
      send(e) {
        return Ks(this, void 0, void 0, function* () {
          return new Promise((t, s) => {
            if (this.isOpen()) {
              const i = new XMLHttpRequest();
              i.open("POST", this.url),
                le(i, "Content-Type", "application/json"),
                (i.onload = () => {
                  i.status >= 200 && i.status < 300
                    ? t(e)
                    : s(Error(i.responseText));
                }),
                (i.onerror = () => {
                  s(Error(ze.NetworkFailure));
                }),
                this.qe(i, JSON.stringify(e)).catch(s);
            } else s(Error(ze.ConnectionNone));
          });
        });
      }
      updateConnectionUrl(e) {
        this.url = ge(
          e.URI,
          { channelId: e.channelId, userId: e.userId },
          e.isTLS
        );
      }
      Be() {
        return Ks(this, void 0, void 0, function* () {
          var e;
          if (!this.He) {
            (this.He = new C()), this.setState(s);
            try {
              yield this.Ze(), this.re(), this.Ge();
            } catch (e) {
              this.He && (this.He.reject(e), (this.He = null)), this.le();
            }
          }
          return null === (e = this.He) || void 0 === e ? void 0 : e.promise;
        });
      }
      We() {
        return (
          this.Ue ||
            (this.Ye.abort(),
            (this.Ue = new C()),
            this.setState(o),
            setTimeout(() => {
              this.le();
            }, 100)),
          this.Ue.promise
        );
      }
      Ze() {
        return new Promise((e, t) => {
          const s = new XMLHttpRequest();
          s.open("POST", this.url),
            le(s, "Content-Type", "application/json"),
            (s.onload = () => {
              s.status >= 200 && s.status < 300
                ? e()
                : t(Error(s.responseText));
            }),
            (s.onerror = () => {
              t(Error(ze.NetworkFailure));
            }),
            this.qe(s, JSON.stringify(De)).catch((e) => {
              t(e);
            });
        });
      }
      Ge() {
        this.isOpen() &&
          (this.Ve >= 5 && ((this.Ve = 0), this.close().catch(() => {})),
          (this.Ye = new XMLHttpRequest()),
          this.Ye.open("GET", this.url),
          (this.Ye.onload = () => {
            (this.Ve = 0),
              200 === this.Ye.status && this.Je(this.Ye.responseText),
              this.Ge();
          }),
          (this.Ye.onerror = () => {
            this.Ve++, this.Ge();
          }),
          this.qe(this.Ye).catch(() => {
            this.Ge();
          }));
      }
      qe(e, t) {
        return Ks(this, void 0, void 0, function* () {
          if (this.authService) {
            const t = yield this.authService.get();
            le(e, "Authorization", `Bearer ${t.token}`);
          }
          e.send(t);
        });
      }
      Je(e) {
        try {
          JSON.parse(e).forEach((e) => {
            this.pe(JSON.parse(e));
          });
        } catch (e) {
          this.ge(e);
        }
      }
      re() {
        var e, t;
        null === (e = this.He) || void 0 === e || e.resolve(),
          (this.He = null),
          null === (t = this.Ue) || void 0 === t || t.reject(),
          (this.Ue = null),
          this.setState(i),
          this.dispatcher.trigger(_t.Open, void 0);
      }
      le() {
        var e;
        null === (e = this.Ue) || void 0 === e || e.resolve(),
          (this.Ue = null),
          (this.He = null),
          this.setState(r),
          this.dispatcher.trigger(_t.Close, void 0);
      }
      pe(e) {
        this.dispatcher.trigger(_t.Message, e),
          this.dispatcher.trigger(_t.MessageReceived, e);
        const t = e.messagePayload;
        if (t.type === Oe.ExecuteApplicationActionCommand) {
          const e = t;
          this.dispatcher.trigger(e.actionType, e);
        }
      }
      ge(e) {
        this.dispatcher.trigger(_t.Error, e);
      }
    }
    var Qs = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const ei = 3e6;
    class ti extends Et {
      constructor(e) {
        super(e.dispatcher),
          (this.He = null),
          (this.Ue = null),
          (this.Ke = !1),
          (this.Xe = !1),
          (this.Qe = !1),
          (this.et = 0),
          (this.tt = !1),
          (this.Ze = () => {
            try {
              (this.st = new WebSocket(this.url)),
                (this.st.onopen = this.ot),
                (this.st.onclose = this.rt),
                (this.st.onerror = this.nt),
                (this.st.onmessage = this.ct);
            } catch (e) {
              this.ht();
            }
          }),
          (this.ot = () =>
            Qs(this, void 0, void 0, function* () {
              (this.tt = !1),
                this.authService && (yield this.lt()),
                this.setState(i),
                this.re();
            })),
          (this.rt = (e) => {
            this.dt(),
              this.Ke
                ? (this.setState(r), this.ut(ze.ConnectionExplicitClose, e))
                : this.authService && !this.Qe && 1006 !== e.code
                ? (this.setState(r), this.ut(ze.AuthExpiredToken, e))
                : this.tt || this.ht(e);
          }),
          (this.nt = (e) => {
            this.ht(), (this.tt = !0), this.ge(e);
          }),
          (this.ct = (e) => {
            try {
              const t = JSON.parse(e.data);
              if (((e) => Ke(e) && e.state.type === Re)(t)) this.Xe = !0;
              else if (ii(t) && this.gt) this.gt.resolve(t.suggestions);
              else {
                this.dispatcher.trigger(_t.Message, t),
                  this.dispatcher.trigger(_t.MessageReceived, t);
                const e = t.messagePayload;
                if (e.type === Oe.ExecuteApplicationActionCommand) {
                  const t = e;
                  this.dispatcher.trigger(t.actionType, t);
                }
              }
            } catch (e) {
              this.ge(e);
            }
          }),
          (this.ge = (e) => {
            this.dispatcher.trigger(_t.Error, e);
          }),
          (this.st = null),
          (this.url = e.url),
          (this.authService = e.authService),
          (this.bt = e.retryInterval),
          (this.ft = e.retryMaxAttempts);
      }
      open() {
        return Qs(this, void 0, void 0, function* () {
          if (!this.isOpen()) {
            if (navigator.onLine)
              return (
                this.He || ((this.He = new C()), this.setState(s), this.Ze()),
                this.He.promise
              );
            throw Error(ze.NetworkOffline);
          }
        });
      }
      close() {
        return Qs(this, void 0, void 0, function* () {
          var e;
          if (!this.isClosed())
            return (
              (this.Ke = !0),
              clearTimeout(this.wt),
              this.Ue ||
                (null === (e = this.st) || void 0 === e || e.close(),
                (this.Ue = new C()),
                this.setState(o)),
              this.Ue.promise
            );
        });
      }
      send(e) {
        return Qs(this, void 0, void 0, function* () {
          var t, s;
          if (
            (null === (t = this.st) || void 0 === t ? void 0 : t.readyState) !==
            i
          )
            throw Error(ze.ConnectionNone);
          this.Qe = !0;
          try {
            return (
              this.st.send(JSON.stringify(e)),
              (Ke((s = e)) && s.state.type === Fe) ||
                (this.dispatcher.trigger(_t.Message, e),
                this.dispatcher.trigger(_t.MessageSent, e)),
              Promise.resolve(e)
            );
          } catch (e) {
            throw Error(ze.NetworkFailure);
          }
        });
      }
      updateConnectionUrl(e) {
        this.url = ue(
          e.URI,
          { channelId: e.channelId, userId: e.userId },
          e.isTLS,
          e.channel
        );
      }
      setSuggestionPromise(e) {
        this.gt = e;
      }
      ht(e) {
        this.setState(s),
          this.et < this.ft
            ? (this.et++, (this.wt = setTimeout(this.Ze, this.bt)))
            : (this.setState(r), this.ut(ze.NetworkFailure, e));
      }
      ut(e, t) {
        var s;
        null === (s = this.He) || void 0 === s || s.reject(Error(e)),
          (this.He = null),
          this.le(t);
      }
      lt() {
        return Qs(this, void 0, void 0, function* () {
          var e, t;
          this.Qe = !1;
          try {
            const e = yield this.authService.get();
            yield this.send(
              ((t = e.token), { state: { token: t, tokenType: Ne, type: je } })
            ),
              setTimeout(() => (this.Qe = !0), 1e4);
          } catch (t) {
            null === (e = this.He) || void 0 === e || e.reject(Error(t)),
              (this.He = null);
            try {
              yield this.close();
            } catch (e) {}
          }
        });
      }
      re() {
        var e, t, s;
        this.dt(),
          clearTimeout(this.wt),
          (this.vt = this.xt()),
          (this.kt =
            ((s = this),
            setTimeout(() => {
              si(s);
            }, ei))),
          (this.et = 0),
          (this.Ke = !1),
          (this.Qe = !1),
          null === (e = this.He) || void 0 === e || e.resolve(),
          (this.He = null),
          null === (t = this.Ue) || void 0 === t || t.reject(),
          (this.Ue = null),
          this.dispatcher.trigger(_t.Open, void 0);
      }
      le(e) {
        var t;
        (this.et = 0),
          (this.Ke = !1),
          (this.Qe = !1),
          null === (t = this.Ue) || void 0 === t || t.resolve(),
          (this.Ue = null),
          this.dispatcher.trigger(_t.Close, e);
      }
      xt() {
        return setInterval(() => {
          this.send(De)
            .then(() => {
              (this.Xe = !1), this.yt();
            })
            .catch(() => {});
        }, 3e4);
      }
      yt() {
        this.zt = setTimeout(() => {
          this.isOpen() && !this.Xe && si(this);
        }, 1e4);
      }
      dt() {
        clearTimeout(this.kt), clearInterval(this.vt), clearTimeout(this.zt);
      }
    }
    function si(e) {
      return Qs(this, void 0, void 0, function* () {
        try {
          yield e.close(), yield e.open();
        } catch (t) {
          si(e);
        }
      });
    }
    const ii = (e) => l(e) && "suggestions" in e;
    var oi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class ri {
      constructor(e) {
        (this.$t = e),
          (this.Ct = 0),
          (this.St = () =>
            oi(this, void 0, void 0, function* () {
              try {
                yield this.It.close(), (this.It = this.Mt), yield this.open();
              } catch (e) {}
            })),
          e.isLongPoll &&
            ((this.$t.retryInterval = 2e3), (this.$t.retryMaxAttempts = 5)),
          (this.oe = e.dispatcher),
          (this.Mt = new ti({
            authService: e.authService,
            url: ue(e.baseURL, e.searchParams, e.isTLS, e.channel),
            retryInterval: e.retryInterval,
            retryMaxAttempts: e.retryMaxAttempts,
            dispatcher: this.oe,
          })),
          (this.It = this.Mt);
      }
      open() {
        return oi(this, void 0, void 0, function* () {
          try {
            yield this.It.open(),
              this.$t.isLongPoll && this.It === this.Mt && this.Tt();
          } catch (e) {
            if (this.$t.isLongPoll && this.It !== this.At)
              return (
                (this.It = this._t()), yield this.It.open(), void this.Et()
              );
            throw e;
          }
        });
      }
      close() {
        return clearInterval(this.Ct), this.It.close();
      }
      send(e) {
        return this.It.send(e);
      }
      isOpen() {
        return this.It.isOpen();
      }
      isClosed() {
        return this.It.isClosed();
      }
      getState() {
        return this.It.getState();
      }
      updateConnectionUrl(e) {
        var t;
        (this.$t = Object.assign(Object.assign({}, this.$t), {
          baseURL: e.URI,
          searchParams: { channelId: e.channelId, userId: e.userId },
          isTLS: e.isTLS,
          channel: e.channel,
        })),
          this.Mt.updateConnectionUrl(e),
          null === (t = this.At) || void 0 === t || t.updateConnectionUrl(e);
      }
      on(e, t) {
        this.oe.bind(e, t);
      }
      off(e, t) {
        this.oe.unbind(e, t);
      }
      setSuggestionPromise(e) {
        this.Mt.setSuggestionPromise(e);
      }
      Tt() {
        var e;
        clearInterval(this.Ct),
          (null === (e = this.At) || void 0 === e ? void 0 : e.isOpen()) &&
            this.At.close();
      }
      _t() {
        return (
          this.At ||
            (this.At = new Xs({
              url: ge(this.$t.baseURL, this.$t.searchParams, this.$t.isTLS),
              authService: this.$t.authService,
              dispatcher: this.oe,
            })),
          this.At
        );
      }
      Et() {
        this.Ct = setInterval(() => {
          this.St();
        }, 3e5);
      }
    }
    const ai = { isLongPoll: !1, isTLS: !0 };
    var ni = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class ci {
      constructor(e) {
        (this.Ot = () => {
          this.open().catch((e) => {
            var t;
            null === (t = this.ae.dispatcher) ||
              void 0 === t ||
              t.trigger(_t.Error, e);
          });
        }),
          (this.Pt = () => {
            this.close().catch((e) => {
              var t;
              null === (t = this.ae.dispatcher) ||
                void 0 === t ||
                t.trigger(_t.Error, e);
            });
          }),
          (this.Lt = (e, t, s) =>
            (!!e && e !== this.ae.URI) ||
            (!!t && t !== this.ae.channelId) ||
            (!!s && s !== this.ae.userId)),
          (this.ae = Object.assign(Object.assign({}, ai), e));
        const t = this.ae;
        t.tokenGenerator && (this.ne = w.getInstance()),
          (this.ce = new ri({
            baseURL: t.URI,
            isLongPoll: t.isLongPoll,
            isTLS: t.isTLS,
            channel: t.channel,
            retryInterval:
              void 0 !== t.retryInterval && t.retryInterval >= 0
                ? 1e3 * t.retryInterval
                : 5e3,
            retryMaxAttempts:
              void 0 !== t.retryMaxAttempts && t.retryMaxAttempts >= 0
                ? t.retryMaxAttempts
                : 5,
            searchParams: { channelId: t.channelId, userId: t.userId },
            authService: this.ne,
            dispatcher: t.dispatcher,
          })),
          window.addEventListener("online", this.Ot),
          window.addEventListener("offline", this.Pt);
      }
      open(e) {
        return ni(this, void 0, void 0, function* () {
          const { URI: t, userId: s, channelId: i } = null != e ? e : {};
          if (this.isOpen()) {
            if (!this.Lt(t, i, s) && !this.ne) return;
            yield Promise.all([this.jt(t, i, s), this.close()]);
          } else yield this.jt(t, i, s);
          yield this.ce.open();
        });
      }
      close() {
        return this.ce.close();
      }
      getState() {
        return this.ce.getState();
      }
      isOpen() {
        return this.ce.isOpen();
      }
      send(e, t, s) {
        return ni(this, void 0, void 0, function* () {
          let i;
          if (
            ((i =
              "string" == typeof e
                ? Qe(e, t)
                : Ze(e)
                ? et(e)
                : qe(e)
                ? tt(e)
                : e),
            !xt(i))
          )
            throw Error(ze.MessageInvalid);
          if (s) {
            const { sdkMetadata: e, threadId: t } = s;
            e && (i = this.Ft(i, e)), t && (i.threadId = t);
          }
          return (
            (i.userId = this.ae.userId),
            this.ae.enableCancelResponse ? (i = st(i)) : delete i.requestId,
            this.ce.send(i)
          );
        });
      }
      updateUser(e, t) {
        return ni(this, void 0, void 0, function* () {
          let s = e;
          return (
            (null == t ? void 0 : t.sdkMetadata) &&
              (s = this.Ft(e, t.sdkMetadata)),
            this.ce.send(s)
          );
        });
      }
      sendDeviceToken(e, t) {
        return ni(this, void 0, void 0, function* () {
          const s = {
            state: {
              type: "token",
              deviceToken: e,
              deviceType: t,
              "store.undelivered.messages": !1,
              "notify.undelivered.skill.messages": !1,
            },
          };
          yield this.ce.send(s);
        });
      }
      cancelRequest(e) {
        console.debug("Requested to cancel", e);
      }
      getSuggestions(e) {
        return ni(this, void 0, void 0, function* () {
          const t = new C();
          this.ce.setSuggestionPromise(t);
          let s = {
            messagePayload: { query: e, threshold: 30, type: Oe.Suggest },
          };
          return (
            this.ae.enableCancelResponse && (s = st(s)),
            this.ce.send(s).catch(null == t ? void 0 : t.reject),
            setTimeout(() => {
              null == t || t.reject(Ot(ze.SuggestionsTimeout));
            }, 1e4),
            null == t ? void 0 : t.promise
          );
        });
      }
      Ft(e, t) {
        return (
          t &&
            (e.sdkMetadata = Object.assign(
              Object.assign({}, e.sdkMetadata),
              t
            )),
          e
        );
      }
      jt(e, t, s) {
        return ni(this, void 0, void 0, function* () {
          const i = this.ae;
          if ((pe(e) && (i.URI = e), this.ne)) {
            const e = yield this.ne.get();
            (i.channelId = e.getClaim("channelId")),
              (i.userId = e.getClaim("userId"));
          } else pe(t) && (i.channelId = t), pe(s) && (i.userId = s);
          this.ce.updateConnectionUrl({
            URI: i.URI,
            channelId: i.channelId,
            userId: i.userId,
            isTLS: i.isTLS,
            channel: i.channel,
          });
        });
      }
    }
    var hi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const li = { oracle: "oracle", platform: "platform" },
      pi = li.oracle;
    class di {
      constructor(e) {
        var t, s, i, o;
        (this.ae = e),
          (this.Rt = null),
          (this.Nt = new Map()),
          (this.Dt = !1),
          (null !== (t = (i = this.ae).dispatcher) && void 0 !== t) ||
            (i.dispatcher = G()),
          (this.ae.URI = be(e.URI)),
          e.tokenGenerator ||
            (null !== (s = (o = this.ae).userId) && void 0 !== s) ||
            (o.userId = ae({ prefix: "user" })),
          this.Ht(e);
      }
      connect(e) {
        return (
          e &&
            ((this.Dt = !0),
            e.URI && (e.URI = be(e.URI)),
            (this.ae = Object.assign(Object.assign({}, this.ae), e))),
          this.Ut.open(e)
        );
      }
      disconnect() {
        return this.Ut.close();
      }
      getState() {
        return this.Ut.getState();
      }
      isConnected() {
        return this.Ut.isOpen();
      }
      sendMessage(e, t) {
        return hi(this, void 0, void 0, function* () {
          var s, i;
          if (!e) throw Error(ze.MessageInvalid);
          let o = "",
            r = "";
          if ("string" == typeof e) r = e;
          else if (qe(e)) {
            r = e.text;
          }
          return (
            (null === (s = this.Rt) || void 0 === s ? void 0 : s.text) === r &&
              (o = this.Rt.requestId),
            (this.Rt = null),
            this.Ut.send(
              e,
              o,
              Object.assign(Object.assign({}, t), {
                threadId:
                  null !== (i = null == t ? void 0 : t.threadId) && void 0 !== i
                    ? i
                    : this.Vt,
              })
            )
          );
        });
      }
      sendAttachment(e, t) {
        return hi(this, void 0, void 0, function* () {
          const s = yield this.uploadAttachment(e, t);
          return this.Ut.send(s, "", {
            sdkMetadata: null == t ? void 0 : t.sdkMetadata,
          });
        });
      }
      sendLocation(e) {
        return hi(this, void 0, void 0, function* () {
          if (!this.isConnected()) throw Error(ze.ConnectionNone);
          if (!e) {
            const { latitude: t, longitude: s } = yield Rt();
            e = { latitude: t, longitude: s };
          }
          if (
            !(function (e) {
              const { latitude: t, longitude: s } = e;
              return ce(t) && ce(s) && ne(t, -90, 90) && ne(s, -180, 180);
            })(e)
          )
            throw Error(ze.LocationInvalid);
          const t = { messagePayload: { type: Oe.Location, location: e } };
          return this.Ut.send(t);
        });
      }
      sendDeviceToken(e, t) {
        return hi(this, void 0, void 0, function* () {
          return this.Ut.sendDeviceToken(e, t);
        });
      }
      sendUserTypingStatus(e, t) {
        return hi(this, void 0, void 0, function* () {
          return this.sendMessage(
            tt({
              partyType: "user",
              source: "sdk",
              status: e,
              type: Oe.Status,
              text: t,
            })
          );
        });
      }
      updateChatContext(e, t, s, i) {
        return hi(this, void 0, void 0, function* () {
          return this.sendMessage(
            {
              messagePayload: Object.assign(
                {
                  type: Oe.UpdateApplicationContextCommand,
                  source: Pe.ChatWindow,
                  context: e,
                },
                t
              ),
            },
            { sdkMetadata: i, threadId: s }
          );
        });
      }
      updateUser(e, t) {
        return hi(this, void 0, void 0, function* () {
          if (!l((s = e)) || !l(s.profile)) throw Error(ze.ProfileInvalid);
          var s;
          return this.Ut.updateUser(
            e,
            Object.assign(Object.assign({}, t), { threadId: this.Vt })
          );
        });
      }
      uploadAttachment(e, t) {
        return hi(this, void 0, void 0, function* () {
          if (!this.isConnected()) throw Error(ze.ConnectionNone);
          if (!this.Bt) throw Error(ze.UploadNotAvailable);
          const { fileName: s, type: i, url: o } = yield this.Bt.upload(e, t);
          return Xe(i, o, s);
        });
      }
      getSuggestions(e) {
        return hi(this, void 0, void 0, function* () {
          if (!e) throw Error(ze.SuggestionsEmptyRequest);
          if ("string" != typeof e) throw Error(ze.SuggestionsInvalidRequest);
          return this.Ut.getSuggestions(e);
        });
      }
      setCurrentThreadId(e) {
        this.Vt = e;
      }
      cancelRequest(e) {
        this.Ut.cancelRequest(e);
      }
      destroy() {
        this.disconnect();
        for (const e in this) this[e] && delete this[e];
      }
      setTTSService(e) {
        this.Wt = "string" == typeof e ? this.qt(e) : e;
      }
      getTTSService() {
        return this.Wt;
      }
      getTTSVoices() {
        return hi(this, void 0, void 0, function* () {
          if (!this.Wt) throw Error(ze.TtsNotAvailable);
          return this.Wt.getVoices();
        });
      }
      setTTSVoice(e) {
        return hi(this, void 0, void 0, function* () {
          if (!this.Wt) throw Error(ze.TtsNotAvailable);
          return this.Wt.setVoice(e);
        });
      }
      getTTSVoice() {
        if (!this.Wt) throw Error(ze.TtsNotAvailable);
        return this.Wt.getVoice();
      }
      speakTTS(e, t) {
        if (this.Wt) {
          let s;
          if ("string" == typeof e) s = e;
          else {
            if (!xt(e)) return;
            s = ct(e, t);
          }
          this.Wt.speak(s);
        }
      }
      cancelTTS() {
        var e;
        null === (e = this.Wt) || void 0 === e || e.cancel();
      }
      startRecognition(e) {
        return hi(this, void 0, void 0, function* () {
          if (!this.Zt) throw Error(ze.RecognitionNotAvailable);
          if (!this.isConnected()) throw Error(ze.ConnectionNone);
          const t = (t) => {
              "final" === t.type && (this.Rt = t),
                null == e || e.onRecognitionText(t);
            },
            s = (t) => {
              var s;
              null === (s = null == e ? void 0 : e.onVisualData) ||
                void 0 === s ||
                s.call(e, t);
            },
            i = () => {
              this.off(_t.ASRResponse, t),
                this.off(_t.ASRVisualData, s),
                this.off(_t.ASRStop, i);
            };
          return (
            this.on(_t.ASRResponse, t),
            this.on(_t.ASRVisualData, s),
            this.on(_t.ASRStop, i),
            this.Zt.startRecognition()
          );
        });
      }
      stopRecognition() {
        return hi(this, void 0, void 0, function* () {
          if (!this.Zt) throw Error(ze.RecognitionNotAvailable);
          return this.Zt.stopRecognition();
        });
      }
      setRecognitionLocale(e) {
        e &&
          "string" == typeof e &&
          this.Zt &&
          this.Zt.setLocale(e.toLowerCase());
      }
      on(e, t) {
        var s;
        null === (s = this.ae.dispatcher) || void 0 === s || s.bind(e, t);
      }
      off(e, t) {
        var s;
        null === (s = this.ae.dispatcher) || void 0 === s || s.unbind(e, t);
      }
      getAuthToken() {
        var e;
        return null === (e = this.ne) || void 0 === e ? void 0 : e.get();
      }
      Ht(e) {
        this.Gt(e),
          this.Yt(e),
          this.Jt(e),
          this.Kt(e),
          (this.Zt = os.getInstance());
      }
      Gt(e) {
        e.tokenGenerator &&
          ((this.ne = w.getInstance()), this.ne.setFetch(e.tokenGenerator));
      }
      Yt(e) {
        var t;
        (this.Ut = new ci(e)),
          null === (t = this.ae.dispatcher) ||
            void 0 === t ||
            t.bind(_t.Open, () => {
              var e, t, s;
              const i = this.ae;
              null === (e = this.Bt) ||
                void 0 === e ||
                e.setConfig(i).catch((e) => {
                  console.warn(e);
                }),
                null === (t = this.Zt) ||
                  void 0 === t ||
                  t.setConfig(i).catch((e) => {
                    console.warn(e);
                  }),
                this.Dt &&
                  (null === (s = this.Wt) ||
                    void 0 === s ||
                    s.setConfig(i).catch((e) => {
                      console.warn(e);
                    }),
                  (this.Dt = !1));
            });
      }
      Jt(e) {
        e.enableAttachment && (this.Bt = Ys.getInstance());
      }
      Kt(e) {
        if (e.isTTS) {
          let t;
          const s = e.TTSService;
          (t = s ? ("string" == typeof s ? this.qt(s) : s) : this.qt(pi)),
            (this.Wt = t);
        }
      }
      qt(e) {
        const t = this.Nt.get(e);
        if (t) return t;
        let s;
        try {
          e === li.oracle
            ? (s = new Ns(this.ae))
            : e === li.platform && (s = new ws()),
            this.Nt.set(e, s);
        } catch (e) {
          console.log(e);
        }
        return s;
      }
    }
    di.TTS = li;
    const ui = Object.assign(Object.assign({}, _t), {
      CHAT_END: "chatend",
      CHAT_LANG: "chatlanguagechange",
      CLICK_AUDIO_RESPONSE_TOGGLE: "click:audiotoggle",
      CLICK_ERASE: "click:erase",
      CLICK_SEARCH_BAR_PINNING: "click:searchbarpinning",
      CLICK_VOICE_TOGGLE: "click:voicetoggle",
      DESTROY: "destroy",
      MESSAGE: "message",
      MESSAGE_RECEIVED: "message:received",
      MESSAGE_SENT: "message:sent",
      NETWORK: "networkstatuschange",
      READY: "ready",
      TYPING: "typing",
      UNREAD: "unreadCount",
      WIDGET_CLOSED: "widget:closed",
      WIDGET_OPENED: "widget:opened",
      WIDGET_SHOW: "widget:show",
      WIDGET_HIDE: "widget:hide",
    });
    class gi {}
    (gi.GEOLOCATION_REQUEST_DENIED = 1),
      (gi.CHAT_SCROLL_DELAY = 300),
      (gi.WEBSOCKET_READY_STATE = ["CONNECTING", "OPEN", "CLOSING", "CLOSED"]),
      (gi.WEBSOCKET_CLOSE_EVENT = { CODE: { ABNORMAL_CLOSURE: 1006 } }),
      (gi.ATTACHMENT_HEADER = {
        AUTHORIZATION: "Authorization",
        FILE_AUTH_TYPE: "x-oda-meta-file-authType",
        FILE_IS_PROTECTED: "x-oda-meta-file-isProtected",
        FILE_SIZE: "x-oda-meta-file-size",
      }),
      (gi.MAX_SUGGESTIONS_COUNT = 5),
      (gi.MIN_SUGGESTIONS_COUNT = 1),
      (gi.SUGGESTIONS_COUNT_THRESHOLD = 30),
      (gi.TIME = { MIN_FIFTY: 3e6 });
    const mi = "25.02",
      bi = 1024,
      fi = 26214400,
      wi = 1e3;
    class vi {
      constructor(e) {
        (this.Xt = e),
          (this.Qt = !1),
          (this.ts = (e) => {
            Ci(e) || (e.code === R && (this.close(), e.stopPropagation()));
          }),
          (this.os = (e) => {
            Ci(e) ||
              (e.code === U &&
                (e.target !== this.rs || e.shiftKey
                  ? e.target === this.ns &&
                    e.shiftKey &&
                    (e.preventDefault(), this.rs.focus())
                  : (e.preventDefault(), this.ns.focus())));
          });
      }
      open() {
        if (this.Qt) return;
        const { autoDismiss: e, autoDismissTimeout: t, parent: s } = this.Xt;
        if (!P(s)) return;
        const i = null != t ? t : 1e4;
        (this.cs = document.activeElement),
          (this.Qt = !0),
          s.append(this.render()),
          this.hs(),
          this.ls(),
          e &&
            setTimeout(() => {
              this.close();
            }, i);
      }
      close() {
        if (!this.Qt) return;
        const { domUtil: e, fallbackFocus: t } = this.Xt,
          s = "dialog-out";
        e.addCSSClass(this.ps, s),
          setTimeout(() => {
            this.ds(),
              e.removeCSSClass(this.ps, s),
              this.us.remove(),
              this.cs && this.cs.offsetParent ? this.cs.focus() : t(),
              (this.Qt = !1);
          }, 200);
      }
      render() {
        const {
            title: e,
            description: t,
            domUtil: s,
            icon: i,
            actions: o,
            showDismiss: r,
            dismissLabel: a,
            modeless: n,
          } = this.Xt,
          c = "dialog",
          h = s.createDiv.bind(s),
          l = s.cssPrefix,
          p = h([`${c}-wrapper`]);
        let d;
        n && s.addCSSClass(p, "modeless"), n || (d = h([`${c}-backdrop`]));
        const u = h([`${c}-icon-content-wrapper`, "flex"]),
          g = h([`${c}-content`]),
          m = h([c, "flex"]);
        if ((n || s.addCSSClass(m, "col"), i)) {
          const e = s.createImageIcon({ icon: i }),
            t = h([`${c}-icon`]);
          $i(t, e), $i(u, t);
        }
        const b = `${c}-title`,
          f = s.createTextDiv([b]);
        if (((f.id = `${l}-${b}`), (f.textContent = e), $i(g, f), t)) {
          const e = `${c}-description`,
            i = s.createTextDiv([e]);
          (i.id = `${l}-${e}`),
            (i.textContent = t),
            $i(g, i),
            m.setAttribute("aria-describedby", i.id);
        }
        if (($i(u, g), $i(m, u), r)) {
          const e = `${c}-close-button`,
            t = s.createIconButton({
              css: [e],
              icon: _a,
              title: a,
              iconCss: [`${e}-icon`],
            });
          Zn(t, zi, this.close.bind(this)), $i(m, t);
        }
        if (o && o.length) {
          const e = h(["action-wrapper", "flex"]);
          o.forEach((t) => {
            const i = ["popup-action"];
            t.type === xi && i.push(xi);
            const o = s.createButton(i);
            (o.innerHTML = t.label),
              Zn(o, zi, (e) => {
                t.handler(e);
              }),
              e.appendChild(o);
          }),
            $i(m, e);
        }
        return (
          n || $i(p, d),
          $i(p, m),
          Nn(m, {
            role: "alertDialog",
            "aria-modal": (!n).toString(),
            "aria-labelledby": f.id,
          }),
          (this.ps = m),
          (this.us = p),
          this.gs(m),
          p
        );
      }
      gs(e) {
        const t = e.querySelectorAll("[tabIndex]:not([tabIndex^='-']), button");
        (this.ns = t[0]), (this.rs = t[t.length - 1]);
      }
      hs() {
        this.ns.focus();
      }
      ls() {
        const e = this.ps;
        Zn(e, ki, this.os), Zn(e, yi, this.ts);
      }
      ds() {
        const e = this.ps;
        Gn(e, ki, this.os, !0), Gn(e, yi, this.ts, !0);
      }
    }
    const xi = "filled",
      ki = "keydown",
      yi = "keyup",
      zi = "click",
      $i = (e, ...t) => {
        e.append(...t);
      },
      Ci = (e) => e.ctrlKey || e.metaKey || e.altKey,
      Si = "aria",
      Ii = `${Si}-expanded`,
      Mi = `${Si}-selected`,
      Ti = `${Si}-activedescendant`,
      Ai = "autocomplete-active";
    class _i {
      constructor(e, t, s) {
        (this.bs = e),
          (this.fs = s),
          (this.ws = -1),
          (this.vs = this.xs(t)),
          Nn(e, {
            "aria-autocomplete": "list",
            "aria-controls": t,
            [Ii]: "false",
            autocomplete: "off",
            role: "combobox",
          });
      }
      display(e, t) {
        this.ks(),
          (this.$t = e.map((s, i) => {
            const o = this.ys(i, e.length);
            return (
              this.zs(o, s, t),
              (o.onclick = () => {
                (this.bs.value = s), this.hide();
              }),
              this.vs.appendChild(o),
              o
            );
          })),
          this.bs.setAttribute(Ii, "true");
      }
      hide() {
        this.bs.setAttribute(Ii, "false"),
          this.bs.removeAttribute(Ti),
          this.ks();
      }
      isOpen() {
        return "true" === this.bs.getAttribute(Ii);
      }
      handleKeyboardEvent(e) {
        let t = !1;
        if (e.ctrlKey) return t;
        const s = this.$t.length;
        switch (e.code) {
          case F:
          case N:
          case U:
            this.$s && Oi(this.bs, this.$s.textContent), this.hide();
            break;
          case H:
            (this.ws = (this.ws + 1) % s), (t = !0);
            break;
          case D:
            (this.ws = this.ws < 0 ? s - 1 : (this.ws - 1 + s) % s), (t = !0);
            break;
          case R:
            this.hide(), this.bs.focus();
        }
        return (
          t &&
            (e.stopPropagation(),
            e.preventDefault(),
            this.Cs(this.$t[this.ws])),
          t
        );
      }
      getListbox() {
        return this.vs;
      }
      xs(e) {
        const t = this.fs.createElement("ul", ["autocomplete-items"]);
        return (
          (t.id = e),
          Nn(t, {
            "aria-labelledby": `${this.bs.id}-label`,
            "aria-live": "polite",
            role: "listbox",
          }),
          Zn(t, "keydown", (e) => {
            this.bs.dispatchEvent(new KeyboardEvent(e.type, e));
          }),
          t
        );
      }
      ys(e, t) {
        const s = this.fs.createElement("li", ["autocomplete-item"]);
        return (
          (s.id = `${this.vs.id}item-${e + 1}`),
          (s.tabIndex = -1),
          Nn(s, {
            "aria-posinset": (e + 1).toString(),
            "aria-setsize": t.toString(),
            [Mi]: "false",
            role: "option",
          }),
          s
        );
      }
      zs(e, t, s) {
        const i = t.toLowerCase().indexOf(s),
          o = this.fs.createTextSpan();
        if ((o.setAttribute("aria-hidden", "true"), i >= 0)) {
          const e = Ei(t.substring(0, i)),
            r = this.fs.createElement("strong", ["strong"], !0);
          r.textContent = t.substring(i, i + s.length);
          const a = Ei(t.substring(i + s.length));
          o.append(e, r, a);
        } else o.textContent = t;
        e.append(o), e.setAttribute("aria-label", t);
      }
      Cs(e) {
        const t = this.$s;
        t && (this.fs.removeCSSClass(t, Ai), t.setAttribute(Mi, "false")),
          e &&
            (e.scrollIntoView(!1),
            e.setAttribute(Mi, "true"),
            this.fs.addCSSClass(e, Ai),
            (this.$s = e),
            this.bs.setAttribute(Ti, e.id));
      }
      ks() {
        const e = this.vs;
        for (; e.firstChild; ) e.removeChild(e.lastChild);
        (this.$t = []), (this.$s = null), (this.ws = -1);
      }
    }
    const Ei = (e) => document.createTextNode(e),
      Oi = (e, t) => {
        (e.value = t), e.setSelectionRange(t.length, t.length);
      };
    class Pi {
      remove() {
        this.element.remove();
      }
      isVisible() {
        return P(this.element);
      }
      appendToElement(e) {
        e.appendChild(this.element);
      }
      prependToElement(e) {
        const t = e.firstChild;
        t ? e.insertBefore(this.element, t) : e.appendChild(this.element);
      }
      appendContentChildElement(e) {
        this.Ss().appendChild(e);
      }
      appendContentChild(e) {
        this.Ss().appendChild(e.element);
      }
      Ss() {
        return this.element;
      }
    }
    var Li = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class ji {
      constructor(e, t, s) {
        var i, o;
        (this.action = e),
          (this.util = t),
          (this.$t = s),
          (this.Is = !1),
          (this.Ms = () => ({
            getPayload: this.Ts,
            label: this.As,
            imageUrl: this._s || this.Es,
            type: this.Os,
          })),
          (this.Ts = () =>
            Li(this, void 0, void 0, function* () {
              return this.action;
            })),
          (this.Os = e.type),
          (this.As = e.label),
          (this.Es = e.imageUrl),
          (this.Ps = e.style),
          (this.Ls = e.tooltip),
          (this.js = e.displayType),
          (this._s =
            null === (i = e.channelExtensions) || void 0 === i
              ? void 0
              : i.activeImageUrl),
          (this.Fs =
            null === (o = e.channelExtensions) || void 0 === o
              ? void 0
              : o.c2kText),
          this.Os !== $e.SubmitForm || this.Ps || (this.Ps = Ce);
      }
      render() {
        const e = this.util,
          t = e.createButton([
            "action-postback",
            this.Ps === Ce ? "primary" : this.Ps === Se ? "danger" : "",
          ]);
        if (
          (this.js === Ie && e.addCSSClass(t, Ie),
          (t.onclick = this.handleOnClick.bind(this)),
          this.Es &&
            t.appendChild(
              e.createImageIcon({ icon: this.Es, iconCss: ["action-image"] })
            ),
          this.As)
        ) {
          const s = Qn(this.As, e.cssPrefix),
            i = e.createTextDiv();
          if (this.js === Me) {
            const o = e.createAnchor("", s);
            (o.onclick = (e) => e.preventDefault()),
              i.appendChild(o),
              e.addCSSClass(t, "display-link");
          } else
            this.Fs
              ? ((i.innerHTML = String.fromCharCode(parseInt(this.As) + 10111)),
                e.addCSSClass(t, "c2k-action"),
                t.addEventListener("mouseover", () => {
                  i.innerHTML = String.fromCharCode(parseInt(this.As) + 10121);
                  for (const t of Array.from(
                    document.getElementsByClassName(this.Fs)
                  ))
                    e.addCSSClass(t, "highlight");
                }),
                t.addEventListener("mouseleave", () => {
                  i.innerHTML = String.fromCharCode(parseInt(this.As) + 10111);
                  for (const t of Array.from(
                    document.getElementsByClassName(this.Fs)
                  ))
                    e.removeCSSClass(t, "highlight");
                }))
              : (i.innerHTML = s);
          t.appendChild(i);
        }
        if ((this.Is && e.addCSSClass(t, "disabled"), this.Ls)) {
          const s = e.createDiv(["action-wrapper"]),
            i = e.createDiv(),
            o = e.createTextDiv(["tooltip", "none"]);
          return (
            (o.innerText = this.Ls),
            o.setAttribute("role", "tooltip"),
            i.appendChild(o),
            s.appendChild(t),
            s.appendChild(i),
            s
          );
        }
        return (this.Rs = t), t;
      }
      disable() {
        (this.Is = !0),
          this.Rs &&
            (this.util.addCSSClass(this.Rs, "disabled"),
            (this.Rs.disabled = !0));
      }
      enable() {
        (this.Is = !1),
          this.Rs &&
            (this.util.removeCSSClass(this.Rs, "disabled"),
            (this.Rs.disabled = !1));
      }
      getActionType() {
        return this.Os;
      }
      handleOnClick(e) {
        var t, s;
        if (this.Is) return;
        const i = this.Ms();
        if (this._s) {
          const e = this.util.createImage(
            this._s,
            ["action-image"],
            this.As || ""
          );
          this.Rs.lastElementChild.replaceWith(e);
        }
        null === (s = (t = this.$t).onMessageActionClicked) ||
          void 0 === s ||
          s.call(t, i);
      }
    }
    var Fi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Ri extends ji {
      constructor(e, t, s) {
        super(e, t, s),
          (this.Ts = () =>
            Fi(this, void 0, void 0, function* () {
              return this.Ns;
            })),
          (this.Ns = e.phoneNumber);
      }
      render() {
        const e = this.util,
          t = super.render();
        "button" === t.tagName.toLowerCase()
          ? e.addCSSClass(t, "action-call")
          : e.addCSSClass(t.firstElementChild, "action-call");
        const s = e.createAnchor(`tel:${this.Ns}`, "");
        return (
          (t.onclick = () => {
            s.click();
          }),
          t
        );
      }
    }
    var Ni = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Di extends ji {
      constructor(e, t, s) {
        super(e, t, s),
          (this.Ds = e),
          (this.Hs = !1),
          (this.Ms = () =>
            Object.assign(
              {
                getPayload: this.Ts,
                label: this.As,
                type: this.Os,
                actionType: this.Ds.actionType,
              },
              this.Ds.actionType === Le.COPY_MESSAGE_TEXT && {
                onSuccess: this.Us,
              }
            )),
          (this.Ts = () =>
            Ni(this, void 0, void 0, function* () {
              return this.Ds;
            })),
          (this.Us = () => {
            if (this.Hs) return;
            this.Hs = !0;
            const e = this.Rs,
              t = this.util,
              s = e.querySelector("img, svg"),
              i = this.util.createImageIcon({
                icon: rn,
                iconCss: ["action-image"],
              }),
              o = (o = !0) => {
                const r = o ? s : i,
                  a = o ? i : s;
                r &&
                  (t.removeCSSClass(r, "icon-enter"),
                  t.addCSSClass(r, "icon-exit"),
                  setTimeout(() => r.remove(), 200)),
                  a
                    ? setTimeout(
                        () => {
                          e.prepend(a),
                            t.removeCSSClass(a, "icon-exit"),
                            t.addCSSClass(a, "icon-enter"),
                            setTimeout(() => {
                              this.Hs = !1;
                            }, 2e3);
                        },
                        r ? 200 : 0
                      )
                    : (this.Hs = !1);
              };
            o(), setTimeout(() => o(!1), 2e3);
          });
      }
      render() {
        const e = this.util,
          t = super.render();
        return (
          "button" === t.tagName.toLowerCase()
            ? e.addCSSClass(t, "action-client")
            : e.addCSSClass(t.firstElementChild, "action-client"),
          t
        );
      }
    }
    var Hi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Ui extends ji {
      constructor() {
        super(...arguments),
          (this.Ts = () =>
            Hi(this, void 0, void 0, function* () {
              return Rt();
            }));
      }
      render() {
        const e = this.util,
          t = super.render();
        return (
          "button" === t.tagName.toLowerCase()
            ? e.addCSSClass(t, "action-location")
            : e.addCSSClass(t.firstElementChild, "action-location"),
          t
        );
      }
      handleOnClick(e) {
        super.handleOnClick(e), e.preventDefault(), e.stopPropagation();
      }
    }
    var Vi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Bi extends ji {
      constructor(e, t, s, i) {
        super(e, t, s),
          (this.Vs = i),
          (this.Ts = () =>
            Vi(this, void 0, void 0, function* () {
              return this.Bs;
            })),
          (this.Bs = e.popupContent);
      }
      render() {
        const e = this.util,
          t = super.render();
        "button" === t.tagName.toLowerCase()
          ? e.addCSSClass(t, "action-popup")
          : e.addCSSClass(t.firstElementChild, "action-popup");
        const s = (function (e, t, s, i) {
          const o = "none",
            r = e.createDiv(["wrapper", "popup-content-wrapper", o]),
            a = e.createDiv(["popup-dialog"]),
            n = pr.fromMessage(
              s,
              e,
              { messagePayload: t },
              Object.assign(Object.assign({}, i), {
                onMessageActionClicked: (t) => {
                  (t.type !== $e.SubmitForm || n.validateForm()) &&
                    (e.addCSSClass(r, o), i.onMessageActionClicked(t));
                },
              })
            ),
            c = n.render(),
            h = c.querySelector(`.${s.name}-form-message-header:first-child`),
            l = e.createIconButton({
              css: ["header-button"],
              icon: s.icons.close || _a,
              iconCss: [],
              title: "close",
            });
          if (
            (Zn(l, "click", () => e.addCSSClass(r, o)),
            (r.tabIndex = 0),
            Zn(r, "click", (t) => {
              a.contains(t.target) || e.addCSSClass(r, o);
            }),
            Zn(r, "keyup", (t) => {
              t.code === R && (e.addCSSClass(r, o), t.stopPropagation());
            }),
            h)
          )
            h.appendChild(l);
          else {
            const t = e.createDiv(["popup-header", "flex"]);
            t.appendChild(l), a.appendChild(t);
          }
          return a.appendChild(c), r.appendChild(a), r;
        })(e, this.Bs, this.Vs, this.$t);
        return document.body.appendChild(s), (this.us = s), t;
      }
      handleOnClick() {
        const e = this.us;
        this.util.removeCSSClass(e, "none"), e.querySelector("button").focus();
      }
    }
    var Wi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class qi extends ji {
      constructor(e, t, s) {
        super(e, t, s),
          (this.Ts = () =>
            Wi(this, void 0, void 0, function* () {
              return this.Ws;
            })),
          (this.Ws = e.postback);
      }
      handleOnClick(e) {
        super.handleOnClick(e), e.preventDefault(), e.stopPropagation();
      }
    }
    var Zi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Gi extends ji {
      constructor(e, t, s, i) {
        super(e, t, s),
          (this.qs = i),
          (this.Ts = () =>
            Zi(this, void 0, void 0, function* () {
              return this.qs;
            }));
      }
      render() {
        const e = this.util,
          t = super.render();
        return (
          "button" === t.tagName.toLowerCase()
            ? e.addCSSClass(t, "action-share")
            : e.addCSSClass(t.firstElementChild, "action-share"),
          t
        );
      }
      handleOnClick(e) {
        super.handleOnClick(e), e.preventDefault(), e.stopPropagation();
      }
    }
    var Yi = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Ji extends ji {
      constructor(e, t, s) {
        super(e, t, s),
          (this.Ts = () =>
            Yi(this, void 0, void 0, function* () {
              return this.Ws;
            })),
          (this.Ws = e.postback);
      }
    }
    var Ki = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class Xi extends ji {
      constructor(e, t, s, i = !1, o) {
        super(e, t, s),
          (this.Zs = i),
          (this.Gs = o),
          (this.Ts = () =>
            Ki(this, void 0, void 0, function* () {
              return this.be;
            })),
          (this.be = e.url);
      }
      render() {
        const e = this.util,
          t = super.render();
        if (
          ("button" === t.tagName.toLowerCase()
            ? e.addCSSClass(t, "action-url")
            : e.addCSSClass(t.firstElementChild, "action-url"),
          this.be)
        ) {
          const s = e.createAnchor(this.be, "", [], this.Zs, this.Gs);
          t.onclick = () => {
            s.click();
          };
        }
        return t;
      }
    }
    function Qi(e) {
      return e.filter((e) => {
        const t = e.getActionType();
        return t === $e.Postback || t === $e.Location || t === $e.SubmitForm;
      });
    }
    var eo = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const to = "left",
      so = "right";
    class io {
      constructor(e, t, s, i, o, r) {
        (this.settings = e),
          (this.util = t),
          (this.payload = s),
          (this.side = i),
          (this.source = o),
          (this.actions = []),
          (this.globalActions = []),
          (this.Ys = []),
          (this.appendedComponents = []),
          (this.Js = (e) => {
            var t, s;
            Dn(e) &&
              (e.getPayload = () =>
                eo(this, void 0, void 0, function* () {
                  return this.getCopyContent();
                }));
            const i = e;
            (i.messageComponent = this),
              null === (s = (t = this.$t).onMessageActionClicked) ||
                void 0 === s ||
                s.call(t, i);
          }),
          (this.getCopyContent = () =>
            m(this.element.cloneNode(!0), this.Ks, L)),
          (this.Ks = (e) => {
            const t = e.querySelectorAll(`.${this.settings.name}-footer-form`);
            return (
              null == t ||
                t.forEach((e) => {
                  e.remove();
                }),
              e
            );
          }),
          (this.locale = e.locale),
          (this.translations = e.i18n[this.locale]),
          (this.shareText = (function (e) {
            let t = fn;
            switch (e.type) {
              case Oe.Card:
                return (
                  e.cards.forEach((e) => {
                    var s;
                    t += `${
                      (e.title ? `${e.title} - ` : fn) +
                      (e.description ? `${e.description} - ` : fn) +
                      (null !== (s = e.url) && void 0 !== s ? s : fn)
                    }\n`;
                  }),
                  t
                );
              case Oe.Text:
                return e.text;
              case Oe.Attachment:
                return e.attachment.url;
              case Oe.Location:
                const s = e.location;
                return `${s.title ? `${s.title} - ` : fn}${s.latitude}, ${
                  s.longitude
                }`;
              case Oe.Table:
                e.rows.forEach((e) => {
                  e.fields.forEach((e) => {
                    t += On(e);
                  });
                });
                break;
              case Oe.Form:
                e.forms.forEach((e) => {
                  const s = En(e);
                  t += s ? `${s} - ` : fn;
                });
                break;
              case Oe.EditForm:
                const i = e;
                (t = i.title ? `${i.title} - ` : fn),
                  Je(i)
                    ? i.fields.forEach((e) => {
                        t += On(e);
                      })
                    : i.formRows.forEach((e) => {
                        e.columns.forEach((e) => {
                          e.fields.forEach((e) => {
                            t += On(e);
                          });
                        });
                      });
                break;
              case Oe.TableForm:
                const o = e;
                o.rows.forEach((e, s) => {
                  e.fields.forEach((e) => {
                    t += On(e);
                  }),
                    (t += En(o.forms[s]));
                });
            }
            return Rn(t);
          })(s)),
          (this.$t = Object.assign(Object.assign({}, r), {
            shareText: this.shareText,
          })),
          (this.Xs = Object.assign(Object.assign({}, this.$t), {
            onMessageActionClicked: this.Js,
          })),
          r.locale &&
            ((this.locale = r.locale),
            (this.translations = Object.assign(
              Object.assign({}, this.translations),
              this.settings.i18n[r.locale]
            ))),
          s.actions &&
            (this.actions = this.buildActions(s.actions, this.shareText)),
          s.globalActions &&
            (this.globalActions = this.buildActions(
              s.globalActions,
              this.shareText
            )),
          (this.headerText = s.headerText),
          (this.footerText = s.footerText),
          s.footerForm &&
            (this.footerFormComponent = vn(t, s.footerForm, e, this.Xs)),
          (this.Ys = Qi(this.actions).concat(Qi(this.globalActions)));
      }
      hasActions() {
        return (
          this.actions.length > 0 ||
          this.globalActions.length > 0 ||
          (this.appendedComponents.length > 0 &&
            this.appendedComponents.some((e) => e.hasActions()))
        );
      }
      focusFirstAction() {
        var e;
        this.firstActionButton
          ? this.firstActionButton.focus()
          : this.appendedComponents.length &&
            (null ===
              (e = this.appendedComponents.find((e) => e.hasActions())) ||
              void 0 === e ||
              e.focusFirstAction());
      }
      disableActions() {
        this.actions.forEach((e) => {
          e.disable();
        }),
          this.globalActions.forEach((e) => {
            e.disable();
          }),
          this.footerFormComponent && this.footerFormComponent.disableActions(),
          this.appendedComponents.forEach((e) => e.disableActions());
      }
      disablePostbacks() {
        this.Ys.forEach((e) => {
          e.disable();
        }),
          this.footerFormComponent &&
            this.footerFormComponent.disablePostbacks(),
          this.appendedComponents.forEach((e) => e.disablePostbacks());
      }
      enableActions() {
        this.actions.forEach((e) => {
          e.enable();
        }),
          this.globalActions.forEach((e) => {
            e.enable();
          }),
          this.footerFormComponent && this.footerFormComponent.enableActions(),
          this.appendedComponents.forEach((e) => e.enableActions());
      }
      enablePostbacks() {
        this.Ys.forEach((e) => {
          e.enable();
        }),
          this.footerFormComponent &&
            this.footerFormComponent.enablePostbacks(),
          this.appendedComponents.forEach((e) => e.enablePostbacks());
      }
      render(e) {
        const t = this.util;
        this.element && (this.element.innerHTML = "");
        const s = this.element ? this.element : t.createDiv(["message"]);
        s.lang = this.locale;
        const i = t.createDiv(["message-wrapper"]);
        s.appendChild(i), this.renderheader(i);
        const o = this.renderMainContent(i, e);
        this.mainView = o;
        const r = this.settings.displayActionsAsPills ? i : o;
        return (
          this.renderLocalActions(r),
          this.renderFooter(i),
          this.renderFooterForm(i),
          this.renderGlobalActions(s),
          this.setupEmbeddedActions(s),
          this.setLinkAdvisory(s),
          (this.element = s),
          s
        );
      }
      append(e) {
        this.appendedComponents.push(e), this.appendComponent(e);
      }
      appendComponent(e) {
        const t = this.element,
          s = t.querySelector(`${this.settings.name}-message-wrapper`),
          i = this.mainView;
        if (!i) return;
        e.renderMainContent(i);
        const o = this.settings.displayActionsAsPills ? s : i;
        e.renderLocalActions(o),
          e.renderFooter(s),
          e.renderFooterForm(s),
          e.renderGlobalActions(t),
          e.setupEmbeddedActions(t);
      }
      renderheader(e) {
        this.payload.headerText && e.append(this.getHeader());
      }
      renderMainContent(e, t) {
        const s = this.getContent(t);
        return e.append(s), s;
      }
      renderLocalActions(e) {
        const t = this.payload.actions;
        if (t && t.length) {
          const t = this.getActions();
          e.appendChild(t),
            this.firstActionButton ||
              (this.firstActionButton = t.firstElementChild),
            (this.actionsWrapper = t);
        }
      }
      renderFooter(e) {
        this.payload.footerText && e.appendChild(this.getFooter());
      }
      renderFooterForm(e) {
        const t = this.footerFormComponent;
        if (t) {
          const s = this.util.createDiv(["footer-form"]);
          s.appendChild(t.render()), e.appendChild(s);
        }
      }
      renderGlobalActions(e) {
        const t = this.payload.globalActions;
        if (null == t ? void 0 : t.length) {
          const t = this.getGlobalActions();
          e.appendChild(t),
            this.firstActionButton ||
              (this.firstActionButton = t.firstElementChild);
        }
      }
      getHeader() {
        return oo(
          this.headerText,
          "message-header",
          this.util,
          this.settings.embeddedVideo
        );
      }
      getContent(e) {
        const t = this.util.createDiv(["message-bubble"]);
        return (
          (t.style.padding = this.settings.messagePadding || t.style.padding),
          e && t.appendChild(e),
          t
        );
      }
      getActions() {
        const e = this.settings,
          t = e.displayActionsAsPills
            ? ["message-global-actions"]
            : ["message-actions"];
        return (
          "horizontal" !== e.actionsLayout && t.push("col"),
          ro(this.actions, t, this.util)
        );
      }
      getFooter() {
        return oo(
          this.footerText,
          "message-footer",
          this.util,
          this.settings.embeddedVideo
        );
      }
      getGlobalActions() {
        const e = ["message-global-actions"];
        return (
          this.settings.icons.avatarBot && e.push("has-message-icon"),
          "horizontal" !== this.settings.globalActionsLayout && e.push("col"),
          ro(this.globalActions, e, this.util)
        );
      }
      buildActions(e, t) {
        return (function (e, t, s, i, o) {
          const r = [];
          return (
            e.forEach((e) => {
              const a = nr.fromActionPayload(e, t, s, i, o);
              a && r.push(a);
            }),
            r
          );
        })(e, this.util, this.settings, t, this.Xs);
      }
      setupEmbeddedActions(e) {
        if (!this.settings.enableEmbeddedActions) return;
        const t = this.payload.embeddedActions;
        if (!t) return;
        const s = this.util,
          i = "embeddedAction",
          o = e.querySelectorAll(`span.${i}`);
        o &&
          o.forEach((e) => {
            const o = t.find((t) => t.id === e.id);
            if (!o) return;
            const r = [i];
            o.displayType && r.push(`display-${o.displayType}`),
              s.addCSSClass(e, ...r);
            const a = nr.fromActionPayload(
              o,
              s,
              this.settings,
              this.shareText,
              this.Xs
            );
            a && (a.render(), Zn(e, "click", a.handleOnClick.bind(a)));
          });
      }
      setLinkAdvisory(e) {
        const { enableOldLinkAdvisory: t, i18n: s, locale: i } = this.settings;
        this.side === to &&
          !this.$t.isFresh &&
          t &&
          Hn(e, s[i].oldLinkAdvisory);
      }
    }
    function oo(e, t, s, i) {
      const o = s.createDiv(["message-bubble", t]),
        r = s.createTextDiv();
      return (r.innerHTML = Qn(e, s.cssPrefix, i)), o.appendChild(r), o;
    }
    function ro(e, t, s) {
      const i = s.createTextDiv(t);
      return (
        e.forEach((e) => {
          i.appendChild(e.render());
        }),
        i
      );
    }
    class ao {
      static capitalize(e) {
        return e.charAt(0).toUpperCase() + e.slice(1);
      }
      constructor(e, t, s, i, o) {
        (this.settings = e),
          (this.util = t),
          (this.side = i),
          (this.Qs = o),
          (this.be = s.url),
          (this.Os = s.type);
        const r = s.url.split("/");
        (this.ei = s.title || decodeURI(r[r.length - 1])),
          (this.ti = s.filename);
      }
      si(e, t) {
        const s = this.util,
          i = this.settings,
          o = s.createAnchor(e, ""),
          r = s.createIconButton({
            css: ["attachment-control-icon", "attachment-button", "flex"],
            icon: i.icons.download || Oa,
            iconCss: ["attachment-download-icon"],
            title: i.i18n[i.locale].download,
          });
        return (
          o.setAttribute("download", t || ""),
          (o.tabIndex = -1),
          o.appendChild(r),
          o
        );
      }
      createAttachment(e, t) {
        const s = this.util,
          i = this.settings,
          o = s.createDiv(["attachment"]),
          r = s.createDiv(["attachment-placeholder", "flex"]),
          a = s.createDiv(["attachment-icon"]),
          n = s.createImageIcon({ icon: e });
        a.appendChild(n);
        const c = this.ei,
          h = s.createDiv([
            "attachment-footer",
            "flex",
            this.Qs && "with-actions",
          ]),
          l = s.createLabel(["attachment-title"]),
          p = s.createDiv(["attachment-controls", "flex"]);
        if (
          ((l.innerText = c),
          l.setAttribute("title", c),
          h.appendChild(l),
          this.Os === Te.Image)
        ) {
          const e = s.createIconButton({
            css: ["attachment-control-icon", "attachment-button", "flex"],
            icon: i.icons.expandImage || on,
            iconCss: ["attachment-expand-icon"],
            title: i.i18n[i.locale].imageViewerOpen,
          });
          (e.onclick = () => {
            this.createImagePreview(this.be, c);
          }),
            p.appendChild(e);
        }
        if ((this.side === to && p.appendChild(this.si(this.be, this.ti)), t))
          switch (
            (r.appendChild(t),
            (t.onerror = () => {
              t.remove(), r.appendChild(a);
            }),
            this.Os)
          ) {
            case Te.Image:
              (t.onload = () => {
                t.clientHeight > 211 && (r.style.alignItems = "flex-start"),
                  h.appendChild(p);
              }),
                (t.onclick = () => {
                  this.createImagePreview(this.be, this.ei);
                });
              break;
            case Te.Audio:
            case Te.Video:
              t.onloadeddata = () => {
                h.appendChild(p);
              };
          }
        else r.appendChild(a), h.appendChild(p);
        return o.appendChild(r), null == o || o.appendChild(h), o;
      }
      createImagePreview(e, t) {
        const s = this.util,
          i = "image-preview",
          o = this.settings,
          r = s.createDiv([`${i}-wrapper`]),
          a = s.createImage(e, [i]),
          n = s.createLabel([`${i}-title`]);
        n.innerText = t;
        const c = document.querySelector(`.${this.settings.name}-wrapper`),
          h = o.icons.close || _a,
          l = s.createIconButton({
            css: [`${i}-close`],
            icon: h,
            iconCss: [`${i}-close-icon`],
            title: o.i18n[o.locale].imageViewerClose,
          });
        (l.onclick = () => {
          r.remove();
        }),
          (l.onkeydown = (e) => {
            "Tab" === e.code && (r.focus(), e.preventDefault());
          });
        const p = s.createDiv([`${i}-header`]);
        p.appendChild(n),
          p.appendChild(l),
          r.appendChild(p),
          r.appendChild(a),
          r.setAttribute("tabindex", "-1"),
          (r.onkeydown = (e) => {
            "Escape" === e.code && r.remove();
          }),
          c.appendChild(r),
          r.focus();
      }
    }
    class no extends ao {
      render() {
        const e = this.util,
          t = this.settings,
          s = t.icons.fileAudio || Ca,
          i = e.createMedia("video", this.be, ["attachment-audio"]);
        (i.controls = !0),
          (i.preload = "metadata"),
          so === this.side && i.setAttribute("controlsList", "nodownload");
        const o = `<a href="${this.be}">`,
          r = t.i18n[t.locale].attachmentAudioFallback
            .replace("{0}", o)
            .replace("{/0}", "</a>");
        return (
          (i.innerHTML = r),
          t.linkHandler
            ? Cn(i, t.linkHandler)
            : t.openLinksInNewWindow && Sn(i),
          this.createAttachment(s, i)
        );
      }
    }
    class co extends ao {
      render() {
        const e = this.settings.icons.fileGeneric || Ra;
        return this.createAttachment(e);
      }
    }
    class ho extends ao {
      render() {
        const e = this.util,
          t = this.settings.icons.fileImage || Na,
          s = e.createImage(this.be, ["attachment-image"], this.ei);
        return this.createAttachment(t, s);
      }
    }
    class lo extends ao {
      render() {
        const e = this.util,
          t = this.settings,
          s = this.be,
          i = t.icons.fileVideo || tn,
          o = cc(s, e.cssPrefix);
        if (o) {
          const t = e.createElement("span");
          return (t.innerHTML = o), t;
        }
        const r = e.createMedia("video", this.be, ["attachment-video"]);
        (r.controls = !0),
          (r.preload = "metadata"),
          so === this.side && r.setAttribute("controlsList", "nodownload");
        const a = `<a href="${this.be}">`,
          n = t.i18n[t.locale].attachmentVideoFallback
            .replace("{0}", a)
            .replace("{/0}", "</a>");
        return (
          (r.innerHTML = n),
          this.settings.linkHandler
            ? Cn(r, t.linkHandler)
            : this.settings.openLinksInNewWindow && Sn(r),
          this.createAttachment(i, r)
        );
      }
    }
    class po extends io {
      static fromPayload(e, t, s, i, o, r = !1) {
        if (
          o &&
          o.authToken &&
          o.uri &&
          s.url.includes(o.uri) &&
          !this.ii.test(s.url)
        ) {
          const e = null == o ? void 0 : o.authToken;
          (null == e ? void 0 : e.length) && (s.url = `${s.url}?token=${e}`);
        }
        switch (s.type) {
          case Te.Image:
            return new ho(e, t, s, i, r);
          case Te.Video:
            return new lo(e, t, s, i, r);
          case Te.Audio:
            return new no(e, t, s, i, r);
          case Te.File:
            return new co(e, t, s, i, r);
          default:
            throw Error("Payload contains wrong attachment type");
        }
      }
      constructor(e, t, s, i, o, r) {
        super(e, t, s, i, o, r),
          (this.oi = po.fromPayload(
            e,
            t,
            s.attachment,
            i,
            r,
            this.hasActions()
          ));
      }
      getContent() {
        return super.getContent(this.oi.render());
      }
    }
    po.ii = /token=[a-z\.\d]+/i;
    class uo extends io {
      constructor(e, t, s, i, o, r) {
        super(e, t, s, i, o, r),
          (this.ri = []),
          (this.cssPrefix = e.name),
          (this.$t = r),
          (this.Ds = s);
      }
      disableActions() {
        super.disableActions(),
          this.ri.forEach((e) => {
            e.disable();
          });
      }
      disablePostbacks() {
        super.disablePostbacks(),
          Qi(this.ri).forEach((e) => {
            e.disable();
          });
      }
      enableActions() {
        super.enableActions(),
          this.ri.forEach((e) => {
            e.enable();
          });
      }
      enablePostbacks() {
        super.enablePostbacks(),
          Qi(this.ri).forEach((e) => {
            e.enable();
          });
      }
      render() {
        return super.render();
      }
      getHeader() {
        const e = this.util,
          t = super.getHeader();
        return e.addCSSClass(t, "message-header-yellow"), t;
      }
      getContent(e) {
        const t = this.util,
          s = "message-bubble",
          i = this.Ds.type,
          o = t.createDiv([s]);
        i === Oe.Table || i === Oe.TableForm
          ? t.addCSSClass(o, `${s}-tabular-message`)
          : t.addCSSClass(
              o,
              `${s}-form-message`,
              i === Oe.EditForm ? "edit-form-message" : ""
            ),
          e && o.appendChild(e);
        const r = this.getPageStatus();
        return r && o.appendChild(r), o;
      }
      getPageStatus() {
        const e = this.util;
        let t;
        const s = this.Ds.paginationInfo;
        return (
          s &&
            s.totalCount > s.rangeSize &&
            ((t = e.createTextDiv(["results-page-status"])),
            (t.innerText = s.status)),
          t
        );
      }
    }
    class go {
      constructor(e, t, s, i, o, r) {
        (this.Vs = e),
          (this.fs = t),
          (this.ai = s),
          (this.$t = o),
          (this.ni = r),
          (this.isTableField = !1),
          (this.isColumnField = !1),
          s.displayType === _e.Action &&
            (this.action = nr.fromActionPayload(s.action, t, e, i, this.$t));
      }
      render() {
        var e;
        const t = this.fs,
          s = this.ai,
          i = (this.isTableField ? "table" : "form") + "-message",
          o = this.$t,
          r = this.Vs,
          {
            alignment: a,
            label: n,
            labelFontSize: c,
            labelFontWeight: h,
            marginTop: l,
            onHoverPopupContent: p,
          } = s,
          d = t.createTextDiv([`${i}-value`]),
          u = null === (e = s.value) || void 0 === e ? void 0 : e.toString();
        switch (s.displayType) {
          case _e.Link:
            const e = t.createDiv(),
              { imageUrl: i, linkLabel: o } = s,
              c = t.createAnchor(u, o ? "" : "ellipsis");
            if (i) {
              const e = t.createImage(i, ["video-wrapper"], u);
              (e.alt = o || ""),
                c.appendChild(e),
                n && t.addCSSClass(d, "with-top-margin");
            } else c.innerHTML = o || be(u) || "";
            c.setAttribute("target", "_blank"),
              e.appendChild(c),
              r.linkHandler
                ? Cn(e, r.linkHandler)
                : r.openLinksInNewWindow && Sn(e),
              d.appendChild(c);
            break;
          case _e.Text:
            const { fontSize: h, fontWeight: l, truncateAt: p } = s;
            u && p
              ? ((d.innerHTML = `${u.slice(0, p)}...`), (d.title = u))
              : (d.innerHTML = u || ""),
              mo(d, h, l, t);
            break;
          case _e.Media:
            const g = s.mediaType,
              m = n && u;
            switch (g) {
              case "image":
                const e = t.createImage(u, ["video-wrapper"], u);
                m && t.addCSSClass(d, "with-top-margin"), d.appendChild(e);
                break;
              case "video":
                cc(u, t.cssPrefix)
                  ? ((d.innerHTML = Qn(u, t.cssPrefix, r.embeddedVideo)),
                    r.embeddedVideo && m && t.addCSSClass(d, "with-top-margin"))
                  : d.appendChild(wo(g, u, d, m, t));
                break;
              case "audio":
                d.appendChild(wo(g, u, d, m, t));
            }
            break;
          case _e.Action:
            t.addCSSClass(d, "flex"),
              (d.style.justifyContent = a),
              n && t.addCSSClass(d, "with-top-margin"),
              d.appendChild(this.action.render());
        }
        if (this.isTableField) return fo(d, p, r, t, o), d;
        const g = `${i}-field`,
          m = [g, `${g}-col-${this.ni}`],
          b = t.createDiv(m),
          f = t.createDiv([`${i}-key`]);
        return (
          (f.innerHTML = n || ""),
          a && ((f.style.textAlign = a), (d.style.textAlign = a)),
          mo(f, c, h, t),
          b.appendChild(f),
          b.appendChild(d),
          fo(b, p, r, t, o),
          this.isColumnField ? bo(b, l, t) : b
        );
      }
      disableActions() {
        this.action.disable();
      }
      disablePostbacks() {
        Qi([this.action]).forEach((e) => {
          e.disable();
        });
      }
      enableActions() {
        this.action.enable();
      }
      enablePostbacks() {
        Qi([this.action]).forEach((e) => {
          e.enable();
        });
      }
    }
    function mo(e, t, s, i) {
      switch (t) {
        case "large":
          i.addCSSClass(e, "font-size-lg");
          break;
        case "small":
          i.addCSSClass(e, "font-size-sm");
          break;
        default:
          i.addCSSClass(e, "font-size-md");
      }
      switch (s) {
        case "bold":
          i.addCSSClass(e, "font-weight-bold");
          break;
        case "light":
          i.addCSSClass(e, "font-weight-light");
          break;
        default:
          i.addCSSClass(e, "font-weight-md");
      }
    }
    function bo(e, t, s) {
      let i = "";
      switch (t) {
        case "none":
          break;
        case "medium":
          i = "margin-top-md";
          break;
        case "large":
          i = "margin-top-lg";
          break;
        default:
          i = "margin-top-default";
      }
      return i && s.addCSSClass(e, i), e;
    }
    function fo(e, t, s, i, o) {
      if (t) {
        const r = pr.fromMessage(s, i, { messagePayload: t }, o);
        if (r) {
          const t = i.createDiv(),
            s = i.createDiv(["popupContent"]);
          s.appendChild(r.render()),
            s.setAttribute("role", "tooltip"),
            t.appendChild(s),
            (e.style.cursor = "pointer"),
            e.appendChild(t);
        }
      }
    }
    const wo = (e, t, s, i, o) => {
      const r = o.createMedia(e, t, ["video-wrapper"]);
      return (
        (r.controls = !0),
        (r.preload = "metadata"),
        i && o.addCSSClass(s, "with-top-margin"),
        r
      );
    };
    class vo extends uo {
      getContent() {
        const e = this.util,
          t = this.settings,
          s = this.Ds,
          i = "form-message",
          o = e.createDiv([i]);
        s.formColumns > 2 && (s.formColumns = 2);
        const r = s.forms;
        return (
          r.forEach((a, n) => {
            if (a.title) {
              const t = e.createTextDiv([`${i}-header`]);
              (t.innerText = a.title), o.appendChild(t);
            }
            const [c, h] = xo(a, s.formColumns, e, t, this.$t);
            this.ri = this.ri.concat(h);
            const l = n + 1;
            l === r.length || r[l].title || e.addCSSClass(c, "with-border"),
              o.appendChild(c);
          }),
          super.getContent(o)
        );
      }
    }
    function xo(e, t, s, i, o) {
      var r;
      const a = "form-message",
        n = `${a}-actions-col`,
        c =
          null === (r = e.channelExtensions) || void 0 === r
            ? void 0
            : r.c2kReferences,
        h = s.createDiv([`${a}-item`, c ? "c2k-reference" : ""]),
        l = o.shareText || En(e, !0),
        p = (function (e, t, s, i, o) {
          var r;
          const a = [];
          if (
            (null === (r = e.actions) || void 0 === r ? void 0 : r.length) > 0
          )
            for (const r of e.actions) {
              const e = nr.fromActionPayload(r, t, s, i, o);
              e && a.push(e);
            }
          return a;
        })(e, s, i, l, o);
      let d;
      if (
        (p.length &&
          (d = (function (e, t, s, i) {
            const o = t.createDiv(
              "horizontal" !== s.formActionsLayout
                ? ["form-actions", "col", i]
                : ["form-actions"]
            );
            for (const t of e) {
              const e = t.render();
              o.appendChild(e);
            }
            return o;
          })(p, s, i, n)),
        Ye(e)
          ? e.formRows.forEach((e, t) => {
              const r = ko(e, p, s, i, l, o),
                a = e.columns.length;
              if (
                (e.columns.forEach((e) => {
                  const t = zo(e, s);
                  e.fields.forEach((r) => {
                    if (It(r)) {
                      const n = new go(i, s, r, l, o);
                      (n.isColumnField = !0),
                        n.action && p.push(n.action),
                        $o(e.width, r.displayType, t, a),
                        t.appendChild(n.render());
                    }
                  }),
                    r.appendChild(t);
                }),
                c && 0 !== t)
              ) {
                const e = s.createTextSpan(["delimiter"]);
                (e.innerHTML = "&bull;"),
                  r.firstElementChild.firstElementChild.lastElementChild.prepend(
                    e
                  );
              }
              h.appendChild(r);
            })
          : e.fields.forEach((e) => {
              const r = new go(i, s, e, l, o, t);
              r.action && p.push(r.action), h.appendChild(r.render());
            }),
        d && h.appendChild(d),
        e.selectAction)
      ) {
        yo(
          nr.fromActionPayload(e.selectAction, s, i, l, o),
          p,
          h,
          e.selectAction.label
        );
      }
      return [h, p];
    }
    function ko(e, t, s, i, o, r) {
      const a = s.createDiv(["form-row", e.separator ? "separator" : ""]);
      if (e.selectAction) {
        yo(
          nr.fromActionPayload(e.selectAction, s, i, o, r),
          t,
          a,
          e.selectAction.label
        );
      }
      return a;
    }
    function yo(e, t, s, i) {
      e &&
        (t.push(e),
        (s.onclick = (t) => e.handleOnClick(t)),
        (s.title = i || ""),
        (s.style.cursor = "pointer"));
    }
    function zo(e, t) {
      const { width: s, verticalAlignment: i } = e,
        o = t.createDiv(["form-row-column", s || ""]);
      return (
        "center" === i
          ? t.addCSSClass(o, "align-center")
          : "bottom" === i
          ? t.addCSSClass(o, "align-end")
          : t.addCSSClass(o, "align-start"),
        o
      );
    }
    function $o(e, t, s, i) {
      "stretch" === e ||
        t !== _e.Media ||
        s.style.maxWidth ||
        (s.style.maxWidth = `calc((100% - ${16 * (i - 1)}px)/${i})`);
    }
    const Co = "aria-expanded",
      So = "";
    class Io extends uo {
      constructor() {
        super(...arguments),
          (this.ci = 0),
          (this.li = 0),
          (this.pi = []),
          (this.di = new ar("EditFormMessageComponent")),
          (this.ui = {}),
          (this.gi = Object.assign(
            Object.assign({}, this.settings.i18n.en),
            this.settings.i18n[this.settings.locale]
          ));
      }
      disableActions() {
        super.disableActions(), Mo(this.mi, this.pi, this.util);
      }
      disablePostbacks() {
        super.disablePostbacks(), Mo(this.mi, this.pi, this.util);
      }
      enableActions() {
        super.enableActions(), Mo(this.mi, this.pi, this.util, !1);
      }
      enablePostbacks() {
        super.enablePostbacks(), Mo(this.mi, this.pi, this.util, !1);
      }
      getContent() {
        const e = this.Ds,
          t = this.settings,
          s = this.util,
          i = "form-message",
          o = `${i}-item`,
          r = s.createDiv([i]),
          a = s.createDiv([o]);
        if (e.title) {
          const t = s.createTextDiv([`${i}-header`]);
          (t.innerText = e.title), r.appendChild(t);
        }
        return (
          Je(e)
            ? (e.formColumns > 2 && (e.formColumns = 2),
              e.fields
                .filter((e) => e)
                .forEach((t) => {
                  a.appendChild(this.bi(t, i, !1, e.formColumns));
                }))
            : e.formRows.forEach((e) => {
                const o = ko(e, this.ri, s, t, this.shareText, this.$t),
                  r = e.columns.length;
                e.columns.forEach((e) => {
                  const t = zo(e, s);
                  e.fields
                    .filter((e) => e)
                    .forEach((s) => {
                      t.appendChild(this.bi(s, i, !0)),
                        $o(e.width, s.displayType, t, r);
                    }),
                    o.appendChild(t);
                }),
                  a.appendChild(o);
              }),
          this.actions
            .concat(this.ri)
            .some((e) => e.getActionType() === $e.SubmitForm) ||
            this.di.error("Payload does not contain submit-form action"),
          this.fi(
            a,
            e.errorMessage ||
              (this.li && this.ci > 1
                ? this.translations.editFormErrorMessage
                : So),
            !0
          ),
          r.appendChild(a),
          (this.wi = a),
          super.getContent(r)
        );
      }
      validateForm() {
        var e;
        let t = !0;
        return (
          null === (e = this.mi) || void 0 === e || e.remove(),
          this.pi.forEach((e) => {
            t = this.xi(e) && t;
          }),
          !t &&
            this.ci > 1 &&
            this.fi(this.wi, this.translations.editFormErrorMessage, !0),
          t
        );
      }
      getSubmittedFields() {
        return (
          this.pi
            .filter((e) => {
              const t = e.tagName.toLowerCase();
              return (
                "textarea" === t && (this.ui[e.id] = e.value), "input" === t
              );
            })
            .forEach((e) => {
              const t = e;
              switch (t.type) {
                case "checkbox":
                  this.ui[t.id] = t.checked
                    ? t.getAttribute("valueOn")
                    : t.getAttribute("valueOff");
                  break;
                case "number":
                  this.ui[t.id] = t.valueAsNumber;
                  break;
                default:
                  this.ui[t.id] = t.value;
              }
            }),
          this.ui
        );
      }
      bi(e, t, s, i) {
        const o = this.shareText,
          r = this.util;
        if ((this.ci++, It(e))) {
          const t = new go(this.settings, r, e, o, this.$t, i);
          return (
            (t.isColumnField = s),
            t.action && this.ri.push(t.action),
            t.render()
          );
        }
        return s
          ? bo(this.ki(e, i, t, r), e.marginTop, r)
          : this.ki(e, i, t, r);
      }
      ki(e, t, s, i) {
        var o, r, a, n, c;
        const h = `${s}-field`,
          l = [h, `${h}-col-${t}`, `edit-${h}`],
          p = i.createDiv(l),
          d = i.createDiv([`${s}-key`, "with-margin"]),
          {
            labelFontSize: u,
            labelFontWeight: g,
            id: m,
            displayType: b,
            placeholder: f,
            required: w,
            clientErrorMessage: v,
            serverErrorMessage: x,
            autoSubmit: k,
          } = e;
        let y, z, $;
        switch (
          ((d.innerHTML = e.label || So), mo(d, u, g, i), p.appendChild(d), b)
        ) {
          case _e.SingleSelect:
            const t = e;
            if (
              ((z = t.defaultValue),
              ($ = t.layoutStyle),
              z && (this.ui[m] = z),
              $ && "list" !== $)
            )
              if ("radioGroup" === $) {
                const e = i.createElement("form", [
                  `${s}-value`,
                  "form-container",
                  "col",
                ]);
                i.setAttributes(e, { id: m, ariaLabel: b, errorMsg: v }),
                  (e.onclick = (e) => e.stopPropagation()),
                  t.options.forEach((t) => {
                    const s = i.createInputElement(
                      {
                        type: "radio",
                        name: m,
                        value: t.label,
                        required: w,
                        checked: t.value === z,
                      },
                      ["radio-input"]
                    );
                    s.onchange = () => {
                      s.checked && (this.ui[m] = t.value), this.yi(m, k, e);
                    };
                    const o = i.createLabel();
                    (o.innerText = t.label), o.prepend(s), e.appendChild(o);
                  }),
                  this.pi.push(e),
                  p.appendChild(e),
                  this.zi(e, w),
                  this.fi(e, x);
              } else
                this.di.error(
                  `Payload contains wrong layout style:${$} for single select field`
                );
            else {
              const e = i.createDiv(["select-wrapper", `${s}-value`]),
                r = i.createInputElement(
                  {
                    type: "text",
                    placeholder: f,
                    required: w,
                    id: m,
                    autocomplete: "off",
                  },
                  [`${s}-value`]
                ),
                a = i.createDiv(),
                n = i.createDiv(["listbox", "popup", "none"]),
                c = i.createElement("ul", ["single-select-list"]),
                h = c.getElementsByTagName("li"),
                l = i.createIconButton({
                  css: ["select-icon"],
                  icon: Sa,
                  iconCss: [],
                  title: So,
                }),
                d = (t) => {
                  "true" !== e.getAttribute(Co) ||
                    a.contains(t.target) ||
                    (y || (r.value = So), g(!1));
                },
                u = () => {
                  "false" === e.getAttribute(Co) &&
                    (e.setAttribute(Co, "true"),
                    i.removeCSSClass(n, "none"),
                    setTimeout(() => document.addEventListener("click", d)),
                    r.focus());
                },
                g = (t = !0) => {
                  "true" === e.getAttribute(Co) &&
                    (y && (r.value = y.textContent || y.innerText),
                    e.setAttribute(Co, "false"),
                    i.addCSSClass(n, "none"),
                    document.removeEventListener("click", d),
                    this.$i(So, h, $),
                    t && r.focus());
                };
              let y,
                $ = [];
              i.setAttributes(e, { errorMsg: v }),
                e.setAttribute(Co, "false"),
                e.setAttribute("aria-label", b),
                (e.onclick = (e) => {
                  e.stopPropagation(), u();
                }),
                (e.oninput = () => {
                  this.$i(r.value, h, $) ? u() : g();
                }),
                (e.onkeydown = (e) => {
                  var t;
                  const s = e.key;
                  s === H || s === D
                    ? !y || y.classList.contains(`${this.cssPrefix}-none`)
                      ? null === (t = $[0]) || void 0 === t || t.focus()
                      : null == y || y.focus()
                    : (s !== R && s !== U) || g();
                }),
                (r.onfocus = () => i.addCSSClass(e, "focus")),
                (r.onblur = () => i.removeCSSClass(e, "focus")),
                (l.onclick = (t) => {
                  t.stopPropagation(),
                    "true" === e.getAttribute(Co) ? g() : u();
                }),
                null === (o = t.options) ||
                  void 0 === o ||
                  o.forEach((t) => {
                    const s = i.createListItem(
                      t.label,
                      t.label,
                      t.label,
                      So,
                      So,
                      () => {
                        i.addCSSClass(s, "selected"),
                          y && i.removeCSSClass(y, "selected"),
                          (y = s),
                          g(),
                          (this.ui[m] = t.value),
                          this.yi(m, k, e);
                      },
                      !1,
                      !1
                    );
                    (s.onkeydown = (e) => this.Ci(e, s, c, r, $)),
                      t.value === z &&
                        (i.addCSSClass(s, "selected"),
                        (y = s),
                        (r.value = t.label)),
                      c.appendChild(s);
                  }),
                ($ = Array.from(h)),
                (a.onclick = (e) => e.stopPropagation()),
                e.appendChild(r),
                e.appendChild(l),
                n.appendChild(c),
                a.appendChild(n),
                p.appendChild(e),
                p.appendChild(a),
                this.pi.push(e),
                this.Si(r.parentElement, w),
                this.fi(r, x);
            }
            break;
          case _e.MultiSelect:
            const h = e;
            if (
              ((z = h.defaultValue),
              ($ = h.layoutStyle),
              (this.ui[m] = z || []),
              $ && "list" !== $)
            )
              if ("checkboxes" === $) {
                const e = i.createElement("form", [
                  `${s}-value`,
                  "form-container",
                  "col",
                ]);
                i.setAttributes(e, {
                  id: m,
                  ariaLabel: b,
                  errorMsg: v,
                  ariaRequired: w ? "true" : "false",
                }),
                  (e.onclick = (e) => e.stopPropagation()),
                  h.options.forEach((t) => {
                    const s = i.createInputElement(
                        {
                          type: "checkbox",
                          name: m,
                          value: t.label,
                          checked: null == z ? void 0 : z.includes(t.value),
                          required: w,
                        },
                        ["radio-input"]
                      ),
                      o = i.createLabel();
                    (o.innerText = t.label),
                      o.prepend(s),
                      (s.onchange = () => {
                        if (s.checked) this.ui[m].push(t.value);
                        else {
                          const e = this.ui[m];
                          e.splice(e.indexOf(t.value), 1);
                        }
                        this.yi(m, k, e);
                      }),
                      e.appendChild(o);
                  }),
                  this.pi.push(e),
                  p.appendChild(e),
                  this.zi(e, w),
                  this.fi(e, x);
              } else
                this.di.error(
                  `Payload contains wrong layout style:${$} for multi select field`
                );
            else {
              const e = i.createDiv([`${s}-value`, "text-field-container"]),
                t = i.createElement("ul", ["selected-options"]),
                o = i.createDiv(),
                a = i.createDiv(["listbox", "popup", "none"]),
                n = [],
                c = i.createDiv(["filter-message-box"]),
                l = i.createDiv(["filter-message-text", "none"]),
                d = i.createInputElement({ type: "text" }, [
                  `${s}-value`,
                  "listbox-search",
                  "none",
                ]),
                u = i.createElement("ul", ["multi-select-list"]),
                g = u.getElementsByTagName("li"),
                b = i.createDiv(["search-icon-wrapper", "none"]),
                y = i.createImageIcon({ icon: qa, iconCss: ["search-icon"] });
              (l.textContent = this.translations.noResultText),
                c.appendChild(l),
                (d.oninput = () =>
                  this.$i(d.value, g, n)
                    ? i.addCSSClass(l, "none")
                    : i.removeCSSClass(l, "none")),
                (d.onkeydown = (t) => {
                  var s;
                  const i = t.key;
                  i === H
                    ? (this.$i(d.value, g, n),
                      null === (s = n[0]) || void 0 === s || s.focus())
                    : (i !== R && i !== U) || e.click();
                }),
                f && t.setAttribute("data-placeholder", f),
                e.setAttribute(Co, "false");
              const $ = (t) => {
                  "true" !== e.getAttribute(Co) || o.contains(t.target) || C();
                },
                C = () => {
                  e.setAttribute(Co, "false"),
                    i.addCSSClass(a, "none"),
                    document.removeEventListener("click", $),
                    (d.value = So),
                    this.$i(d.value, g, n),
                    i.addCSSClass(d, "none"),
                    i.addCSSClass(b, "none"),
                    i.addCSSClass(l, "none");
                };
              (e.onclick = (t) => {
                if ((t.stopPropagation(), "true" === e.getAttribute(Co)))
                  C(), e.focus();
                else {
                  e.setAttribute(Co, "true"), i.removeCSSClass(a, "none");
                  const t = u.firstElementChild;
                  t ? t.focus() : i.removeCSSClass(l, "none"),
                    setTimeout(() => document.addEventListener("click", $));
                }
              }),
                (e.onkeydown = (t) => {
                  const s = t.code;
                  t.ctrlKey ||
                    t.altKey ||
                    t.metaKey ||
                    t.shiftKey ||
                    s === R ||
                    s === U ||
                    (e.click(),
                    i.removeCSSClass(d, "none"),
                    i.removeCSSClass(b, "none"),
                    d.focus());
                }),
                i.setAttributes(e, {
                  id: m,
                  ariaRequired: w ? "true" : "false",
                }),
                (e.tabIndex = 0),
                v && e.setAttribute("data-error", v),
                null === (r = h.options) ||
                  void 0 === r ||
                  r.forEach((s) => {
                    const o = (o) => {
                        const r = i.createDiv(["multi-select-option"]);
                        r.innerText = s.label;
                        const a = i.createImageIcon({
                          icon: _a,
                          iconCss: ["opt-close"],
                        });
                        (a.onclick = () => {
                          t.removeChild(r), u.appendChild(o);
                          const i = this.ui[m];
                          i.splice(i.indexOf(s.value), 1), this.yi(m, k, e);
                        }),
                          r.appendChild(a),
                          (r.onclick = (t) => {
                            t.stopPropagation(),
                              "true" === e.getAttribute(Co) && e.click();
                          }),
                          t.appendChild(r);
                      },
                      r = i.createListItem(
                        s.label,
                        s.label,
                        s.label,
                        So,
                        So,
                        () => {
                          e.click(),
                            u.removeChild(r),
                            this.ui[m].push(s.value),
                            o(r),
                            this.yi(m, k, e);
                        },
                        !1,
                        !1
                      );
                    (r.onkeydown = (t) => this.Ci(t, r, u, e, n)),
                      (null == z ? void 0 : z.includes(s.value))
                        ? o(r)
                        : u.appendChild(r);
                  }),
                (o.onclick = (e) => e.stopPropagation()),
                e.appendChild(t),
                this.pi.push(e),
                p.appendChild(e),
                b.appendChild(y),
                a.appendChild(c),
                a.appendChild(d),
                a.appendChild(b),
                a.appendChild(u),
                o.appendChild(a),
                p.appendChild(o),
                this.Si(e, w),
                this.fi(e, x);
            }
            break;
          case _e.Toggle:
            const l = e,
              d = i.createLabel([`${s}-value`, "toggle"]);
            (d.tabIndex = 0),
              (d.onclick = (e) => e.stopPropagation()),
              (y = i.createInputElement({
                id: m,
                placeholder: f,
                required: w,
                type: "checkbox",
                checked: l.defaultValue === l.valueOn,
                errorMsg: v,
                valueOn: l.valueOn,
                valueOff: l.valueOff,
              }));
            const u = l.labelOn || l.valueOn,
              g = l.labelOff || l.valueOff;
            y.setAttribute("aria-label", y.checked ? u : g),
              (y.oninput = () => {
                y.setAttribute("aria-label", y.checked ? u : g),
                  this.yi(m, k, y);
              }),
              d.appendChild(y),
              d.appendChild(i.createDiv(["round-slider"])),
              p.appendChild(d),
              this.fi(y.parentElement, x);
            break;
          case _e.DatePicker:
            const C = e;
            y = i.createInputElement(
              {
                type: "date",
                id: m,
                title: f,
                required: w,
                defaultValue: C.defaultValue,
                min: C.minDate,
                max: C.maxDate,
                errorMsg: v,
              },
              [`${s}-value`]
            );
            break;
          case _e.TimePicker:
            const S = e;
            y = i.createInputElement(
              {
                type: "time",
                id: m,
                title: f,
                required: w,
                defaultValue: S.defaultValue,
                min: S.minTime,
                max: S.maxTime,
                errorMsg: v,
              },
              [`${s}-value`]
            );
            break;
          case _e.TextInput:
            const I = e;
            if (I.multiLine) {
              const e = i.createElement(
                "textarea",
                ["textarea", `${s}-value`],
                !0
              );
              i.setAttributes(e, {
                id: m,
                required: w,
                minLength: I.minLength,
                maxLength: I.maxLength,
                defaultValue: I.defaultValue,
                placeholder: I.placeholder,
                errorMsg: v,
              }),
                (e.rows = 3),
                (e.onchange = () => this.yi(m, k, e)),
                (e.onclick = (e) => e.stopPropagation()),
                p.appendChild(e),
                this.pi.push(e),
                this.Si(e, w),
                this.fi(e, x);
            } else
              y = i.createInputElement(
                {
                  type: I.inputStyle || "text",
                  id: m,
                  placeholder: f,
                  required: w,
                  defaultValue: I.defaultValue,
                  errorMsg: v,
                  minLength: I.minLength,
                  maxLength: I.maxLength,
                  pattern: I.validationRegularExpression,
                },
                [`${s}-value`]
              );
            break;
          case _e.NumberInput:
            const M = e;
            y = i.createInputElement(
              {
                type: "number",
                id: m,
                placeholder: f,
                required: w,
                defaultValue:
                  null === (a = M.defaultValue) || void 0 === a
                    ? void 0
                    : a.toString(),
                min:
                  null === (n = M.minValue) || void 0 === n
                    ? void 0
                    : n.toString(),
                max:
                  null === (c = M.maxValue) || void 0 === c
                    ? void 0
                    : c.toString(),
                errorMsg: v,
              },
              [`${s}-value`]
            );
            break;
          default:
            this.di.error(
              `Payload contains wrong display type:${b} for editable field`
            );
        }
        return (
          y &&
            ("checkbox" !== y.type &&
              (p.appendChild(y),
              this.Si(y, w),
              this.fi(y, x),
              (y.onchange = () => this.yi(m, k, y)),
              (y.onclick = (e) => e.stopPropagation())),
            this.pi.push(y)),
          p
        );
      }
      xi(e, t = !1) {
        const s = e.dataset.error;
        let i,
          o = e.nextElementSibling,
          r = !0;
        switch (e.tagName.toLowerCase()) {
          case "form":
            const t = e,
              a = t.querySelector("input"),
              n = t.getAttribute("aria-label");
            if (n === _e.MultiSelect && "true" === t.ariaRequired) {
              this.ui[t.id].length ||
                ((r = !1),
                (i = s || (null == a ? void 0 : a.validationMessage)));
            } else
              n !== _e.SingleSelect ||
                t.checkValidity() ||
                ((r = !1),
                (i = s || (null == a ? void 0 : a.validationMessage)));
            break;
          case "input":
            const c = e;
            "checkbox" === c.type
              ? (o = o.parentElement.nextElementSibling)
              : c.checkValidity() || ((i = s || c.validationMessage), (r = !1));
            break;
          case "textarea":
            const h = e;
            h.checkValidity() || ((i = s || h.validationMessage), (r = !1));
            break;
          case "div":
            const l = e;
            if (
              ((o = o.nextElementSibling),
              l.getAttribute("aria-label") === _e.SingleSelect)
            ) {
              const e = l.firstElementChild;
              (r = !e.required || Boolean(this.ui[e.id])),
                r || (i = s || e.validationMessage);
              break;
            }
            "true" === l.getAttribute("aria-required") &&
              ((i = s), (r = Boolean(this.ui[e.id].length)));
        }
        return (
          (() => {
            t ||
              ("SPAN" === (null == o ? void 0 : o.tagName) &&
                (this.util.removeCSSClass(e.parentElement, "error"),
                o.remove(),
                this.li--),
              r || this.fi(e, i || this.translations.editFieldErrorMessage));
          })(),
          r
        );
      }
      $i(e, t, s) {
        const i = this.util;
        s.length = 0;
        for (let o = 0; o < t.length; o++) {
          const r = t[o],
            a = r.querySelector("span"),
            n = r.textContent || r.innerText;
          n.toLowerCase().indexOf(e.toLowerCase()) < 0
            ? (i.addCSSClass(r, "none"),
              (a.innerHTML = n.replace(/(<b>)|(<\/b>)/g, So)))
            : ((a.innerHTML = e
                ? n.replace(new RegExp(`${e}`, "gi"), "<b>$&</b>")
                : n.replace(/(<b>)|(<\/b>)/g, So)),
              i.removeCSSClass(r, "none"),
              s.push(r));
        }
        return s.length > 0;
      }
      Ci(e, t, s, i, o) {
        var r, a, n, c;
        const h = this.cssPrefix,
          l = o.indexOf(t),
          p = o.length;
        let d = !1;
        if (!(e.ctrlKey || e.altKey || e.metaKey)) {
          if (e.shiftKey && e.code === U) i.click();
          else
            switch (e.code) {
              case F:
              case N:
                t.click(), (d = !0);
                break;
              case R:
              case U:
                i.click(), e.code === R && (i.focus(), (d = !0));
                break;
              case D:
                const u = t.previousElementSibling || s.lastElementChild;
                u.classList.contains(`${h}-none`)
                  ? null === (r = o[(l + p - 1) % p]) ||
                    void 0 === r ||
                    r.focus()
                  : u.focus(),
                  (d = !0);
                break;
              case H:
                const g = t.nextElementSibling || s.firstElementChild;
                g.classList.contains(`${h}-none`)
                  ? null === (a = o[(l + 1) % p]) || void 0 === a || a.focus()
                  : g.focus(),
                  (d = !0);
                break;
              case W:
              case B:
                const m = s.firstElementChild;
                m.classList.contains(`${h}-none`)
                  ? null === (n = o[0]) || void 0 === n || n.focus()
                  : m.focus(),
                  (d = !0);
                break;
              case q:
              case V:
                const b = s.lastElementChild;
                b.classList.contains(`${h}-none`)
                  ? null === (c = o[p - 1]) || void 0 === c || c.focus()
                  : b.focus(),
                  (d = !0);
                break;
              default:
                if (i instanceof HTMLInputElement) i.focus();
                else {
                  const e = s.previousElementSibling,
                    t = e.previousElementSibling,
                    i = this.util;
                  i.removeCSSClass(t, "none"),
                    i.removeCSSClass(e, "none"),
                    t.focus();
                }
            }
          d && (e.stopPropagation(), e.preventDefault());
        }
      }
      yi(e, t, s) {
        if (this.xi(s) && t) {
          const t = d(this.getSubmittedFields());
          this.pi.forEach((e) => {
            this.xi(e, !0) || delete t[e.id];
          }),
            Object.keys(t).forEach((e) => {
              const s = t[e];
              Array.isArray(s)
                ? 0 === s.length && delete t[e]
                : 0 === s || s || delete t[e];
            });
          const s = this.settings.sdkMetadata
            ? Object.assign({ version: mi }, this.settings.sdkMetadata)
            : { version: mi };
          this.$t.webCore
            .sendMessage(
              tt({
                submittedFields: t,
                partialSubmitField: e,
                type: Oe.FormSubmission,
              }),
              { sdkMetadata: s }
            )
            .then(() => {
              const e = this.settings.disablePastActions;
              "all" === e
                ? this.disableActions()
                : "postback" === e && this.disablePostbacks();
            })
            .catch((e) =>
              this.di.error(
                "[partialSubmit] Failed to send postback message:",
                e
              )
            );
        }
      }
      fi(e, t, s = !1) {
        if (t) {
          const i = this.util,
            o = i.createTextSpan(["field-error", s ? "form-error" : So]),
            r = i.createImageIcon({ icon: Pa, iconCss: ["form-error-icon"] }),
            a = i.createTextSpan(["error-text"]);
          if (((a.innerText = t), o.appendChild(r), o.appendChild(a), s))
            e.appendChild(o), (this.mi = o);
          else {
            const t = e.parentElement;
            i.addCSSClass(t, "error"), t.appendChild(o), this.li++;
          }
        }
      }
      Si(e, t) {
        this.Ii(e, t, !0);
      }
      zi(e, t) {
        this.Ii(e, t, !1);
      }
      Ii(e, t, s) {
        if (t) {
          const t = this.util,
            i = t.createTextSpan(["field-required-tip" + (s ? "-end" : "")]),
            o = t.createTextSpan(["required-tip-text"]);
          (o.innerText = this.gi.requiredTip), i.appendChild(o);
          e.parentElement.appendChild(i);
        }
      }
    }
    function Mo(e, t, s, i = !0) {
      e && (i ? s.addCSSClass(e, "disabled") : s.removeCSSClass(e, "disabled")),
        t.forEach((e) => {
          switch (e.tagName.toLowerCase()) {
            case "form":
              const t = e.getElementsByTagName("input");
              i
                ? s.addCSSClass(e, "disabled")
                : s.removeCSSClass(e, "disabled");
              for (let e = 0; e < t.length; e++) {
                t[e].disabled = i;
              }
              break;
            case "input":
              const o = e;
              (o.disabled = i),
                "checkbox" === o.type &&
                  (i
                    ? (s.addCSSClass(e.parentElement, "disabled"),
                      (e.parentElement.tabIndex = -1))
                    : (s.removeCSSClass(e.parentElement, "disabled"),
                      (e.parentElement.tabIndex = 0)));
              break;
            case "textarea":
              e.disabled = i;
              break;
            case "div":
              i
                ? ((e.ariaDisabled = "true"),
                  s.addCSSClass(e, "disabled"),
                  s.addCSSClass(e.parentElement, "disabled"))
                : ((e.ariaDisabled = "false"),
                  s.removeCSSClass(e, "disabled"),
                  s.removeCSSClass(e.parentElement, "disabled")),
                1 === e.childElementCount &&
                  "ul" === e.firstElementChild.tagName.toLowerCase() &&
                  (e.tabIndex = i ? -1 : 0),
                2 === e.childElementCount &&
                  "input" === e.firstElementChild.tagName.toLowerCase() &&
                  ((e.firstChild.disabled = i),
                  (e.firstChild.nextSibling.disabled = i));
          }
        });
    }
    const To = 100;
    class Ao extends uo {
      getContent() {
        const e = this.util,
          t = this.Ds,
          s = Eo(t.headings),
          i = "table-message",
          o = e.createDiv([`${i}-wrapper`]),
          r = t.tableTitle;
        if (r) {
          const t = e.createDiv([`${i}-table-title-wrapper`]),
            s = e.createElement("strong", [`${i}-table-title`], !0);
          (s.textContent = r), t.append(s), o.append(t);
        }
        const a = e.createElement("table", [i]);
        o.appendChild(a);
        const n = e.createElement("tr", [`${i}-headings`]);
        return (
          s.forEach((t) => {
            const s = _o(e, [`${i}-heading`], t.width, t.alignment);
            (s.innerText = t.label), n.appendChild(s);
          }),
          a.appendChild(n),
          t.rows.forEach((t) => {
            const o = e.createElement("tr", [`${i}-row`]);
            if (t.selectAction) {
              yo(
                nr.fromActionPayload(
                  t.selectAction,
                  e,
                  this.settings,
                  this.shareText,
                  this.$t
                ),
                this.ri,
                o,
                t.selectAction.label
              );
            }
            t.fields.forEach((t, r) => {
              const a = _o(e, [`${i}-item`], s[r].width, t.alignment),
                n = new go(this.settings, e, t, this.shareText, this.$t);
              (n.isTableField = !0),
                n.action && this.ri.push(n.action),
                a.appendChild(n.render()),
                o.appendChild(a);
            }),
              a.appendChild(o);
          }),
          super.getContent(o)
        );
      }
    }
    function _o(e, t, s, i) {
      const o = e.createElement("td", t, !0);
      return (o.style.textAlign = i), (o.style.width = `${s}%`), o;
    }
    function Eo(e) {
      let t;
      if (e.every((e) => !e.width || (e.width >= 0 && e.width <= To))) {
        let s = 0,
          i = 0;
        if (
          (e.forEach((e) => {
            e.width ? (i += e.width) : s++;
          }),
          s)
        )
          if (i < To) {
            const o = (To - i) / s;
            t = e.map((e) => (e.width || (e.width = o), e));
          } else t = Oo(e);
        else if (i === To) t = e;
        else {
          const s = To / i;
          t = e.map((e) => ((e.width = e.width * s), e));
        }
      } else t = Oo(e);
      return t;
    }
    function Oo(e) {
      const t = To / e.length;
      return e.map((e) => ((e.width = t), e));
    }
    class Po extends uo {
      getContent() {
        const e = this.util,
          t = this.Ds,
          s = Eo(t.headings.concat({ alignment: "center", label: "" })),
          i = "table-message",
          o = e.createDiv([`${i}-wrapper`]),
          r = t.tableTitle;
        if (r) {
          const t = e.createDiv([`${i}-table-title-wrapper`]),
            s = e.createElement("strong", [`${i}-table-title`], !0);
          (s.textContent = r), t.append(s), o.append(t);
        }
        const a = e.createElement("table", [i, "tableform-message"]);
        o.appendChild(a);
        const n = e.createElement("tr", [`${i}-headings`]);
        s.forEach((t) => {
          const s = _o(e, [`${i}-heading`], t.width, t.alignment);
          (s.innerText = t.label), n.appendChild(s);
        }),
          a.appendChild(n);
        return (
          (n.lastElementChild.style.width = "32px"),
          t.rows.forEach((o, r) => {
            const n = e.createElement("tr", [`${i}-row`]);
            o.fields.forEach((t, o) => {
              const r = _o(e, [`${i}-item`], s[o].width, t.alignment),
                a = new go(this.settings, e, t, this.shareText, this.$t);
              (a.isTableField = !0),
                a.action && this.ri.push(a.action),
                r.appendChild(a.render()),
                n.appendChild(r);
            }),
              t.formColumns > 2 && (t.formColumns = 2);
            const c = t.forms[r],
              h = _o(e, [`${i}-item`, "button-cell"]),
              l = e.createIconButton({
                css: [`${i}-item`, `${i}-item-form-toggle`],
                icon: Ia,
                iconCss: [],
                title: c.title || "",
              });
            h.appendChild(l), n.appendChild(h);
            const p = "none",
              d = "rotate-180",
              [u, g] = xo(c, t.formColumns, e, this.settings, this.$t);
            (this.ri = this.ri.concat(g)), e.addCSSClass(u, p);
            let m = !1;
            (n.onclick = () => {
              m
                ? (e.addCSSClass(u, p), e.removeCSSClass(l, d))
                : (e.removeCSSClass(u, p), e.addCSSClass(l, d)),
                (m = !m);
            }),
              a.appendChild(n),
              a.appendChild(u);
          }),
          super.getContent(o)
        );
      }
    }
    var Lo = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    class jo {
      constructor(e, t, s, i) {
        var o;
        (this.Vs = e),
          (this.fs = t),
          (this.$t = i),
          (this.ri = []),
          (this.Ys = []),
          (this.Js = (e) => {
            var t, s;
            e.type === $e.Client &&
              e.actionType === Le.COPY_MESSAGE_TEXT &&
              (e.getPayload = () =>
                Lo(this, void 0, void 0, function* () {
                  return this.getCopyContent();
                }));
            const i = e;
            (i.messageComponent = this),
              null === (s = (t = this.$t).onMessageActionClicked) ||
                void 0 === s ||
                s.call(t, i);
          }),
          (this.getCopyContent = () => {
            var e;
            return L(
              null === (e = this.Mi) || void 0 === e ? void 0 : e.cloneNode(!0)
            );
          }),
          (this.ei = s.title),
          (this.Ti = s.description),
          (this.Es = s.imageUrl),
          (this.be = s.url),
          (null !== (o = s.actions) && void 0 !== o) || (s.actions = []),
          (this.ri = s.actions
            .map((s) => {
              var o;
              const r =
                (this.ei ? `${this.ei} - ` : "") +
                (this.Ti ? `${this.Ti} - ` : "") +
                (null !== (o = this.be) && void 0 !== o ? o : "");
              return nr.fromActionPayload(
                s,
                t,
                e,
                r,
                Object.assign(Object.assign({}, i), {
                  onMessageActionClicked: this.Js,
                })
              );
            })
            .filter(Boolean)),
          (this.Ys = Qi(this.ri));
      }
      render() {
        const e = this.fs,
          t = this.Vs,
          s = t.embeddedVideo,
          i = t.locale,
          o = this.be,
          r = e.createDiv(["card"]),
          a = o
            ? e.createAnchor(
                o,
                "",
                ["card-component"],
                t.openLinksInNewWindow,
                t.linkHandler
              )
            : e.createDiv(["card-content"]);
        if ((this.be && (a.innerText = ""), this.Es)) {
          const s = t.i18n;
          let o = s[i].cardImagePlaceholder;
          if (this.$t && this.$t.locale) {
            const e = s[this.$t.locale];
            o = e ? e.cardImagePlaceholder : o;
          }
          a.appendChild(e.createImage(this.Es, ["card-image"], o));
        }
        const n = e.createTextDiv(["card-title"]);
        if (
          ((n.innerHTML = Qn(this.ei, e.cssPrefix, s)),
          a.appendChild(n),
          this.Ti)
        ) {
          const t = e.createTextDiv(["card-description"]);
          (t.innerHTML = Qn(this.Ti, e.cssPrefix, s)), a.appendChild(t);
        }
        if (
          (r.appendChild(a),
          t.linkHandler
            ? Cn(a, t.linkHandler)
            : t.openLinksInNewWindow && Sn(a),
          this.ri.length > 0)
        ) {
          const s = e.createDiv(
            "horizontal" !== t.cardActionsLayout
              ? ["card-actions", "col"]
              : ["card-actions"]
          );
          let i = !0;
          for (const e of this.ri) {
            const t = e.render();
            i && ((this.Ai = t), (i = !1)), s.appendChild(t);
          }
          r.appendChild(s);
        }
        return (this.Mi = r), r;
      }
      hasActions() {
        return this.ri.length > 0;
      }
      disableActions() {
        this.ri.forEach((e) => e.disable());
      }
      disablePostbacks() {
        this.Ys.forEach((e) => e.disable());
      }
      enableActions() {
        this.ri.forEach((e) => e.enable());
      }
      enablePostbacks() {
        this.Ys.forEach((e) => e.enable());
      }
      getFirstActionButton() {
        return this.Ai;
      }
    }
    class Fo extends io {
      constructor(e, t, s, i, o, r) {
        super(e, t, s, i, o, r),
          (this._i = []),
          (this.Ei = s.layout),
          (this.Oi = s.cards.length),
          s.cards.forEach((e) => {
            this._i.push(new jo(this.settings, t, e, this.$t));
          }),
          (this.globalActions = this.actions.concat(this.globalActions)),
          (this.actions = []),
          (this.Pi = !1),
          (this.Li = !0);
      }
      hasActions() {
        return (
          this._i[0].hasActions() ||
          this.actions.length > 0 ||
          this.globalActions.length > 0
        );
      }
      disableActions() {
        super.disableActions(),
          this._i.forEach((e) => {
            e.disableActions();
          });
      }
      disablePostbacks() {
        super.disablePostbacks(),
          this._i.forEach((e) => {
            e.disablePostbacks();
          });
      }
      enableActions() {
        super.enableActions(),
          this._i.forEach((e) => {
            e.enableActions();
          });
      }
      enablePostbacks() {
        super.enablePostbacks(),
          this._i.forEach((e) => {
            e.enablePostbacks();
          });
      }
      render() {
        const e = this.util,
          t = this.settings.name,
          s = [`card-message-${this.Ei}`],
          i = super.render();
        if (i.querySelector(`.${t}-icon-wrapper`)) {
          s.push("has-message-icon");
          const o = i.querySelector(`.${t}-content-wrapper`);
          e.addCSSClass(o, "with-icon");
        }
        return e.addCSSClass(i, ...s), i;
      }
      setCardsScrollAttributes(e) {
        (this.Pi = "rtl" === getComputedStyle(this.ji).direction),
          (this.Li = "default" === e);
      }
      getContent() {
        const e = this.util,
          t = this.Oi,
          s = e.createDiv(["card-message-content"]),
          i = e.createDiv(["card-message-cards"]);
        let o = !0;
        if (
          (this._i.forEach((e) => {
            const t = e.render();
            o &&
              e.hasActions() &&
              ((this.firstActionButton = e.getFirstActionButton()), (o = !1)),
              i.appendChild(t);
          }),
          s.appendChild(i),
          "horizontal" === this.Ei && t > 1)
        ) {
          let e;
          s.appendChild(this.Fi()),
            (this.Ri = 0),
            i.addEventListener("scroll", () => {
              clearTimeout(e),
                (e = setTimeout(() => {
                  let e = 0;
                  for (let s = 0; s < t; s++) {
                    const o = this.Pi ? t - s - 1 : s,
                      r = i.children[o];
                    if (i.scrollLeft <= r.offsetLeft + 5) {
                      e = o;
                      break;
                    }
                  }
                  e !== this.Ri && ((this.Ri = e), this.Ni());
                }, 100));
            }),
            window.addEventListener(
              "resize",
              An(() => {
                this.Di();
              }, 500)
            );
        }
        (this.Hi = s), (this.ji = i);
        const r = this.settings.name;
        return (
          new IntersectionObserver(
            (e) => {
              e.forEach((e) => {
                e.isIntersecting && this.Di();
              });
            },
            { root: document.querySelector(`.${r}-conversation`) }
          ).observe(i),
          s
        );
      }
      Fi() {
        if (!this.Ui) {
          const e = this.util,
            t = this.translations.cardNavNext;
          this.Ui = e.createDiv(["next-wrapper"]);
          const s = e.createIconButton({
            css: ["round", "next"],
            icon: Ma,
            iconCss: [],
            title: t,
          });
          (s.onclick = this.Vi.bind(this)), this.Ui.appendChild(s);
        }
        return this.Ui;
      }
      Bi() {
        if (!this.Wi) {
          const e = this.util,
            t = this.translations.cardNavPrevious;
          this.Wi = e.createDiv(["prev-wrapper"]);
          const s = e.createIconButton({
            css: ["round", "previous"],
            icon: Ta,
            iconCss: [],
            title: t,
          });
          (s.onclick = this.qi.bind(this)), this.Wi.appendChild(s);
        }
        return this.Wi;
      }
      Vi() {
        this.Ri < this.Oi && (this.Ri++, this.Ni());
      }
      qi() {
        this.Ri > 0 && (this.Ri--, this.Ni());
      }
      Ni() {
        var e, t, s, i;
        const o = this.ji.children[this.Ri];
        if (o) {
          const r = 52,
            a = 68;
          (this.ji.scrollLeft = o.offsetLeft - (this.Li ? r : a)),
            0 === this.Ri
              ? null === (e = this.Wi) || void 0 === e || e.remove()
              : (null === (t = this.Wi) || void 0 === t
                  ? void 0
                  : t.parentElement) || this.Hi.prepend(this.Bi()),
            this.Ri === this.Oi - 1
              ? null === (s = this.Ui) || void 0 === s || s.remove()
              : (null === (i = this.Ui) || void 0 === i
                  ? void 0
                  : i.parentElement) || this.Hi.appendChild(this.Fi());
        }
      }
      Di() {
        this.ji.scrollWidth === this.ji.offsetWidth
          ? (this.Ui && (this.Ui.hidden = !0), this.Wi && (this.Wi.hidden = !0))
          : (this.Ui && (this.Ui.hidden = !1),
            this.Wi && (this.Wi.hidden = !1));
      }
    }
    class Ro extends io {
      constructor(e, t, s, i, o, r) {
        super(e, t, s, i, o, r), (this.Zi = s.text);
      }
      getContent() {
        const e = this.settings,
          t = this.util,
          s = this.Zi,
          i = t.createTextDiv(["message-text"]);
        return (
          this.side === so
            ? Ze(this.payload) && (No(s) || kn(s))
              ? (t.addCSSClass(i, "message-user-postback"), (i.innerHTML = s))
              : (i.textContent = Do(s))
            : ((i.innerHTML = Qn(s, t.cssPrefix, e.embeddedVideo)),
              e.linkHandler
                ? Cn(i, e.linkHandler)
                : e.openLinksInNewWindow && Sn(i)),
          super.getContent(i)
        );
      }
    }
    const No = (e) => !!e && /^<img\s+/i.test(e),
      Do = (e) =>
        e.replace(/&#x([0-9a-f]+);/gi, (e, t) =>
          String.fromCharCode(parseInt(t, 16))
        );
    class Ho extends Ro {
      constructor(e, t, s, i, o, r) {
        super(e, t, { type: Oe.Text, text: s.errorMessage }, i, o, r);
      }
      getContent() {
        const e = super.getContent();
        return this.util.addCSSClass(e, "error"), e;
      }
    }
    class Uo {
      constructor(e) {
        this.fs = e;
      }
      render() {
        const e = this.fs.createDiv(["spinner"]);
        return (
          (e.innerHTML =
            '<svg viewBox="0 0 64 64"><circle transform="translate(32,32)" r="26"></circle></svg>'),
          e
        );
      }
    }
    class Vo {
      constructor(e, t, s, i) {
        (this.Zi = e), (this.Gi = t), (this.Vs = s), (this.fs = i);
      }
      render() {
        const e = this.fs,
          t = this.Vs,
          s = t.icons,
          i = e.createDiv(["attachment"]),
          o = this.Gi === to ? s.avatarBot : s.avatarUser,
          r = e.createDiv(["attachment-footer", "flex"]),
          a = e.createTextDiv(["attachment-title"]);
        (a.innerText = this.Zi), r.appendChild(a);
        const n = e.createDiv(["attachment-placeholder", "flex"]);
        return (
          n.appendChild(new Uo(e).render()),
          i.appendChild(n),
          i.appendChild(r),
          (this.Mi = t.searchBarMode
            ? e.getMessage(i)
            : e.getMessageBlock(this.Gi, i, o)),
          this.Mi
        );
      }
      remove() {
        this.Mi.remove();
      }
    }
    class Bo extends io {
      constructor(e, t, s, i, o, r) {
        super(e, t, s, i, o, r);
        const a = s.location;
        (this.ei = a.title),
          (this.be = a.url),
          (this.Yi = a.longitude),
          (this.Ji = a.latitude);
      }
      render() {
        const e = this.util,
          t = e.createDiv(["message"]);
        t.lang = this.locale;
        const s = e.createDiv(["message-wrapper"]);
        t.appendChild(s);
        const i = e.createDiv(["attachment"]),
          o = e.createDiv(["attachment-placeholder", "flex"]),
          r = e.createDiv(["attachment-icon"]),
          a = e.createImageIcon({
            icon: this.settings.icons.shareMenuLocation || Ja,
          }),
          n = e.createDiv(["attachment-footer", "flex"]),
          c = e.createLabel(["attachment-title"]);
        if (
          ((c.innerText = this.ei
            ? this.ei
            : `${this.Ji.toFixed(4)}, ${this.Yi.toFixed(4)}`),
          n.appendChild(c),
          r.appendChild(a),
          o.appendChild(r),
          !this.actions.length)
        ) {
          const t = e.createDiv(["attachment-controls"]),
            s = e.createIconButton({
              css: ["attachment-control-icon", "attachment-button", "flex"],
              icon: this.settings.icons.externalLink || Fa,
              iconCss: [],
              title: this.translations.openMap,
            }),
            i = e.createAnchor(
              this.be ||
                `https://www.google.com/maps/@${this.Ji},${this.Yi},12z`,
              "",
              [],
              this.settings.openLinksInNewWindow,
              this.settings.linkHandler
            );
          (s.onclick = () => {
            i.click();
          }),
            t.appendChild(s),
            n.appendChild(t);
        }
        return (
          i.appendChild(o),
          i.appendChild(n),
          s.appendChild(this.getContent(i)),
          t
        );
      }
    }
    class Wo {
      constructor(e, t, s, i, o, r = !0) {
        (this.ei = e),
          (this.Zi = t),
          (this.Gi = s),
          (this.Vs = i),
          (this.fs = o),
          (this.Ki = r);
      }
      render(e) {
        const t = this.fs,
          s = this.Vs,
          i = s.icons,
          o = "message",
          r = t.createDiv([`${o}-content`]),
          a = this.Gi === to ? i.avatarBot : i.avatarUser;
        if (e) {
          t.addCSSClass(r, `${o}-with-icon`);
          const s = t.createImageIcon({ icon: e }),
            i = t.createDiv([`${o}-icon`]);
          i.appendChild(s), r.appendChild(i);
        }
        const n = t.createDiv([`${o}-text`]),
          c = t.createTextDiv([`${o}-title`]),
          h = t.createTextDiv([`${o}-description`]);
        return (
          (c.innerText = this.ei),
          (h.innerText = this.Zi),
          n.appendChild(c),
          n.appendChild(h),
          r.appendChild(n),
          s.searchBarMode
            ? t.getMessage(r, this.Ki)
            : t.getMessageBlock(this.Gi, r, a, this.Ki)
        );
      }
    }
    class qo extends io {
      constructor(e, t, s, i, o, r) {
        super(e, t, s, i, o, r), (this.Ds = JSON.stringify(s.payload));
      }
      getContent() {
        const e = this.util.createTextSpan();
        return (e.innerText = this.Ds), super.getContent(e);
      }
    }
    const Zo = setTimeout,
      Go = setInterval,
      Yo = 36e5,
      Jo = 864e5,
      Ko = "relTimeNow",
      Xo = "relTimeMoment";
    class Qo {
      constructor(e, t) {
        (this.fs = t),
          (this.gi = Object.assign(
            Object.assign({}, e.i18n.en),
            e.i18n[e.locale]
          ));
        const s = e.icons,
          i = e.name,
          o = "-has-message-icon";
        (this.Xi = i),
          (this.Qi = `${i}-left ${s.avatarBot ? `${i}${o}` : ""}`),
          (this.eo = `${i}-right ${s.avatarUser ? `${i}${o}` : ""}`);
      }
      render() {
        const e = this.fs;
        let t = this.Mi;
        return (
          t
            ? (t.setAttribute("aria-live", "off"),
              t.setAttribute("aria-hidden", "true"))
            : (t = e.createTextDiv()),
          (t.className = `${this.Xi}-relative-timestamp ${this.so}`),
          (this.Mi = t),
          t
        );
      }
      setLocale(e) {
        if (((this.gi = e), this.io))
          switch (this.io) {
            case Ko:
            case Xo:
              this.oo(e[this.io]);
              break;
            default:
              this.oo(e[this.io].replace("{0}", `${this.ro}`));
          }
      }
      setRelativeTime(e) {
        const t = new Date().getTime() - e.getTime(),
          s = Math.floor(t / 1e3),
          i = Math.floor(s / 60),
          o = Math.floor(i / 60),
          r = Math.floor(o / 24),
          a = Math.floor(r / 30),
          n = Math.floor(a / 12);
        n > 0
          ? this.ao(n)
          : a > 0
          ? this.no(a)
          : r > 0
          ? this.co(r)
          : o > 0
          ? this.ho(o)
          : i > 0
          ? this.lo(i)
          : this.po(s);
      }
      refresh(e) {
        (this.so = e === He ? this.Qi : this.eo),
          (this.Mi.className = `${this.Xi}-relative-timestamp ${this.so}`),
          this.do();
      }
      remove() {
        var e;
        (null === (e = this.Mi) || void 0 === e ? void 0 : e.parentElement) &&
          this.Mi.remove();
      }
      do() {
        this.uo(Ko, 1e4, this.po.bind(this));
      }
      po(e = 10) {
        (e *= 1e3), this.uo(Xo, 6e4 - e, this.lo.bind(this));
      }
      lo(e = 1) {
        this.mo("relTimeMin", 6e4, 60, this.ho.bind(this), e);
      }
      ho(e = 1) {
        this.mo("relTimeHr", Yo, 24, this.co.bind(this), e);
      }
      co(e = 1) {
        this.mo("relTimeDay", Jo, 30, this.no.bind(this), e);
      }
      no(e = 1) {
        this.mo("relTimeMon", 2592e6, 12, this.ao.bind(this), e);
      }
      ao(e = 1) {
        this.mo("relTimeYr", 31536e6, 60, () => {}, e);
      }
      uo(e, t, s) {
        this.bo(),
          this.oo(this.gi[e]),
          (this.io = e),
          (this.fo = Zo(() => {
            s();
          }, t));
      }
      mo(e, t, s, i, o = 1) {
        this.bo(),
          this.oo(this.gi[e].replace("{0}", `${o}`)),
          (this.io = e),
          (this.ro = o),
          (this.fo = Go(() => {
            o++,
              (this.ro = o),
              o > s
                ? (clearInterval(this.fo), i())
                : this.oo(this.gi[e].replace("{0}", `${o}`));
          }, t));
      }
      oo(e) {
        this.Mi || this.render(), (this.Mi.innerText = e);
      }
      bo() {
        clearTimeout(this.fo), clearInterval(this.fo);
      }
    }
    class er extends Ro {
      constructor(e, t, s, i, o, r) {
        super(e, t, s, i, o, r),
          (this.wo = 0),
          (this.vo = s.actions),
          (this.ratingId = Date.now());
      }
      focusFirstAction() {
        this.xo[0].focus();
      }
      disableActions() {
        this.ko(!0), super.disableActions();
      }
      disablePostbacks() {
        this.ko(!0), super.disablePostbacks();
      }
      enableActions() {
        this.ko(!1), super.enableActions();
      }
      enablePostbacks() {
        this.ko(!1), super.enablePostbacks();
      }
      highlightRating(e) {
        if (!this.actions || !this.xo) return;
        const t = this.util,
          s = "active",
          i = "string" == typeof e ? this.yo(e) : e;
        for (let e = 1; e <= this.xo.length; e++) {
          const o = this.xo[e - 1];
          if (!o) break;
          (i && e <= i) || (0 === i && e <= this.wo)
            ? t.addCSSClass(o, s)
            : t.removeCSSClass(o, s);
        }
      }
      getActions() {
        const e = this.util,
          t = this.settings,
          s = t.i18n[t.locale].ratingStar,
          i = e.createDiv(["rating-wrapper"]);
        (this.xo = this.vo.map((o) => {
          const r = e.createElement("input", ["star-input", "rating-hidden"]);
          (r.id = `rating-${o.label}-${this.ratingId}`),
            (r.type = "radio"),
            (r.name = `rating-${this.ratingId}`),
            (r.value = o.label);
          const a = e.createLabel(["star-label"]);
          (a.htmlFor = `rating-${o.label}-${this.ratingId}`),
            a.setAttribute("data-rating", o.label);
          const n = e.createTextSpan(["rating-hidden"]),
            c = s.replace("{0}", `${o.label}`);
          n.innerText = c;
          const h = (t.icons && t.icons.rating) || Wa,
            l = e.createImageIcon({ icon: h, iconCss: ["rating-star-icon"] });
          return (
            a.appendChild(n),
            a.appendChild(l),
            (r.onfocus = () => {
              r.disabled || (this.wo = this.zo(r));
            }),
            (r.onkeydown = (e) => {
              "Enter" === e.key && this.$o(o);
            }),
            (a.onclick = () => {
              r.disabled || ((this.wo = this.zo(a)), this.$o(o));
            }),
            (a.onmouseover = () => {
              r.disabled || this.zo(a);
            }),
            (a.onmouseleave = () => {
              r.disabled || this.zo(null);
            }),
            i.appendChild(r),
            i.appendChild(a),
            r
          );
        })),
          this.wo && this.zo(null);
        const o = e.createDiv(["rating-root"]);
        return o.appendChild(i), o;
      }
      ko(e) {
        this.xo &&
          this.xo.forEach((t) => {
            t.disabled = e;
          });
      }
      $o(e) {
        const t = {
          getPayload: () => Promise.resolve(e.postback),
          label: e.label,
          type: e.type,
        };
        this.Js(t);
      }
      zo(e) {
        let t = 0;
        if (e) {
          const s =
            "value" in e
              ? e.value
              : null == e
              ? void 0
              : e.getAttribute("data-rating");
          t = s ? parseInt(s, 10) : 0;
        }
        return this.highlightRating(t), t;
      }
      yo(e) {
        let t = 0;
        if (/^\d+$/.exec(e)) {
          const s = parseInt(e, 10);
          s > 0 && s <= this.actions.length && (t = s);
        }
        return t;
      }
    }
    const tr = "start",
      sr = "end";
    class ir extends io {
      constructor(e, t, s, i, o, r) {
        var a;
        super(e, t, s, i, o, r),
          (this.Co = ""),
          (this.So = !0),
          (this.Io = s.streamState),
          (this.Zi = s.text),
          (this.Co = s.text),
          (this.So = null !== (a = r.isFresh) && void 0 !== a ? a : this.So);
        let n = "";
        this.Mo = or(
          (s) => {
            n += s;
            const i = n.length % 20 ? n : Qn(n, t.cssPrefix, e.embeddedVideo),
              o = zn(i);
            this.textElement &&
              (this.textElement instanceof HTMLInputElement ||
              this.textElement instanceof HTMLTextAreaElement
                ? (this.textElement.focus(),
                  (this.textElement.value = o),
                  this.textElement instanceof HTMLTextAreaElement &&
                    (this.textElement.scrollTop =
                      this.textElement.scrollHeight))
                : (this.textElement.innerHTML = o));
          },
          () => {
            var e;
            this.Io === sr &&
              (this.isCoPilot
                ? this.showDone()
                : ((this.Zi =
                    null === (e = this.textElement) || void 0 === e
                      ? void 0
                      : e.innerHTML),
                  this.render()));
          },
          e.typingDelay || 1
        );
      }
      update(e) {
        const t = e.streamState;
        switch (((this.Io = t), t)) {
          case tr:
            this.renderClean(e),
              this.isCoPilot && this.Mo.push(e.text.split(""));
            break;
          case "running":
            this.Mo.push(e.text.split("")), (this.Co = e.text);
            break;
          case sr:
            if (((this.payload = e), this.So)) {
              const t = this.Co;
              if (((this.Co = ""), t.length)) {
                const s = e.text.lastIndexOf(t);
                if (s >= 0) {
                  const i = e.text.substring(s + t.length);
                  this.Mo.push(i.split("")),
                    this.isCoPilot || this.setAddOnComponents(e);
                  break;
                }
              }
            }
            this.renderClean(e);
        }
      }
      freeze() {
        return this.Mo.clear(), (this.Co = ""), this.textElement.innerHTML;
      }
      getContent() {
        var e;
        const t = this.settings,
          s = this.util,
          i = s.createTextDiv();
        return (
          i.setAttribute("aria-hidden", "true"),
          !this.So || (this.Io !== tr && this.textElement)
            ? ((i.innerHTML = Qn(this.Zi, s.cssPrefix, t.embeddedVideo)),
              this.Io === sr && i.removeAttribute("aria-hidden"),
              t.linkHandler
                ? Cn(i, t.linkHandler)
                : t.openLinksInNewWindow && Sn(i))
            : ((this.textElement = i),
              this.Mo.push(
                null === (e = this.Zi) || void 0 === e ? void 0 : e.split("")
              )),
          super.getContent(i)
        );
      }
      renderClean(e) {
        this.Mo.clear(),
          (this.Zi = e.text),
          this.isCoPilot || (this.setAddOnComponents(e), this.render());
      }
      setAddOnComponents(e) {
        (this.headerText = e.headerText),
          e.actions && (this.actions = this.buildActions(e.actions)),
          (this.footerText = e.footerText),
          e.footerForm &&
            (this.footerFormComponent = vn(
              this.util,
              e.footerForm,
              this.settings,
              Object.assign(Object.assign({}, this.$t), {
                shareText: this.shareText,
              })
            )),
          e.globalActions &&
            (this.globalActions = this.buildActions(e.globalActions)),
          (this.Ys = Qi(this.actions).concat(Qi(this.globalActions)));
      }
    }
    const or = (e, t, s) => {
      const i = [];
      let o = !0;
      const r = () => {
        if (!i.length) return (o = !0), void setTimeout(() => t());
        setTimeout(() => {
          i.length && (e(i.shift()), r());
        }, s);
      };
      return {
        push: (e) => {
          i.push(...e), o && ((o = !1), r());
        },
        clear: () => {
          i.length = 0;
        },
      };
    };
    class rr extends Pi {
      constructor(e, t, s) {
        super(),
          (this.Gi = e),
          (this.Vs = t),
          (this.fs = s),
          (this.element = this.render()),
          (this.To = !1),
          (this.Ao = !0);
      }
      append(e) {
        if (!this.isVisible() && e) {
          if (this.Vs.searchBarMode) {
            if (!e.firstChild) return;
            e.firstChild.appendChild(this.element);
          } else e.appendChild(this.element);
          (this.To = !0),
            this._o && clearTimeout(this._o),
            this.Ao &&
              (this._o = setTimeout(() => {
                this.remove();
              }, 1e3 * this.Vs.typingIndicatorTimeout));
        }
      }
      remove() {
        this.isVisible() && (this.element.remove(), (this.To = !1));
      }
      isVisible() {
        return this.To;
      }
      render() {
        const e = this.fs,
          t = this.Vs,
          s = e.createDiv(["typing-cue-wrapper"]),
          i = t.icons.avatarBot;
        if (t.icons.typingIndicator) {
          const i = t.icons.typingIndicator,
            o = e.createImageIcon({ icon: i });
          (o.style.height = t.chatBubbleIconHeight || o.style.height),
            (o.style.width = t.chatBubbleIconWidth || o.style.width),
            s.appendChild(o);
        } else {
          const t = e.createDiv(["typing-cue"]);
          s.appendChild(t);
        }
        return (
          s.setAttribute("aria-live", "polite"),
          (this.Hi = s),
          this.updateTypingCueLocale(t.i18n[t.locale].typingIndicator),
          t.searchBarMode ? e.getMessage(s) : e.getMessageBlock(this.Gi, s, i)
        );
      }
      updateTypingCueLocale(e) {
        this.Hi.setAttribute("aria-label", e);
      }
      resetTypingCueIcon() {
        this.element.remove(), (this.element = this.render());
      }
      updateTypingCueIcon(e) {
        (e.style.marginTop = "0px"), this.element.firstChild.replaceWith(e);
      }
      setAutoTimeout(e) {
        this.Ao = e;
      }
    }
    class ar {
      constructor(e) {
        this.Eo = e;
      }
      debug(...e) {
        this.Oo(ar.LOG_LEVEL.DEBUG, e);
      }
      error(...e) {
        this.Oo(ar.LOG_LEVEL.ERROR, e);
      }
      info(...e) {
        this.Oo(ar.LOG_LEVEL.INFO, e);
      }
      warn(...e) {
        this.Oo(ar.LOG_LEVEL.WARN, e);
      }
      Oo(e, t) {
        if (ar.logLevel >= e) {
          let s;
          switch (
            (t.unshift(`[${ar.appName}.${ar.appVersion}.${this.Eo}]`), e)
          ) {
            case ar.LOG_LEVEL.ERROR:
              s = console.error;
              break;
            case ar.LOG_LEVEL.WARN:
              s = console.warn;
              break;
            case ar.LOG_LEVEL.INFO:
              s = console.info;
              break;
            case ar.LOG_LEVEL.DEBUG:
              s = console.debug;
          }
          s.apply(console, t);
        }
      }
    }
    (ar.LOG_LEVEL = { NONE: 0, ERROR: 1, WARN: 2, INFO: 3, DEBUG: 4 }),
      (ar.logLevel = ar.LOG_LEVEL.NONE);
    class nr {
      static fromActionPayload(e, t, s, i, o) {
        switch (e.type) {
          case $e.Postback:
            return new qi(e, t, o);
          case $e.Url:
            return new Xi(e, t, o, s.openLinksInNewWindow, s.linkHandler);
          case $e.Webview:
            return new Xi(
              e,
              t,
              o,
              s.openLinksInNewWindow,
              o.webviewLinkHandler
            );
          case $e.Location:
            return new Ui(e, t, o);
          case $e.Call:
            return new Ri(e, t, o);
          case $e.Share:
            return new Gi(e, t, o, i);
          case $e.SubmitForm:
            return new Ji(e, t, o);
          case $e.Popup:
            return new Bi(e, t, o, s);
          case $e.Client:
            return new Di(e, t, o);
          default:
            return (
              nr.logger.error(`Payload contains wrong action type:${e.type}`),
              null
            );
        }
      }
    }
    function cr(e) {
      return !!e.source;
    }
    function hr(e) {
      if (e.msgId) return e.msgId;
      const t = JSON.stringify(e.messagePayload);
      return `${lr(t)}`;
    }
    nr.logger = new ar("ActionComponentFactory");
    const lr = (e) => {
      let t = 0,
        s = 0;
      const i = Math.pow(9, 9);
      for (; t < e.length; ) s = Math.imul(s ^ e.charCodeAt(t++), i);
      return s ^ (s >>> 9);
    };
    class pr {
      static fromMessage(e, t, s, i) {
        let o, r;
        cr(s) ? ((o = to), (r = s.source || Be)) : (o = so);
        const a = s.messagePayload;
        switch (a.type) {
          case Oe.Postback:
          case Oe.Text:
            return a.channelExtensions &&
              "stars" === a.channelExtensions.displayType
              ? new er(e, t, a, o, r, i)
              : new Ro(e, t, a, o, r, i);
          case Oe.TextStream:
            return new ir(e, t, a, o, r, i);
          case Oe.Error:
            return new Ho(e, t, a, o, r, i);
          case Oe.Attachment:
            return new po(e, t, a, o, r, i);
          case Oe.Card:
            return new Fo(e, t, a, o, r, i);
          case Oe.Location:
            return new Bo(e, t, a, o, r, i);
          case Oe.Table:
            return new Ao(e, t, a, o, r, i);
          case Oe.Form:
            return new vo(e, t, a, o, r, i);
          case Oe.TableForm:
            return new Po(e, t, a, o, r, i);
          case Oe.EditForm:
            return new Io(e, t, a, o, r, i);
          case Oe.Raw:
            return new qo(e, t, a, o, r, i);
          default:
            throw Error(`Wrong message payload type:${a.type}`);
        }
      }
    }
    const dr = "keydown";
    class ur {
      constructor(e) {
        var t;
        (this.Po = new Map()),
          (this.Lo = !0),
          (this.jo = (e) => {
            if (gr(e) && this.Fo(e.code)) {
              const e = document.querySelector(this.Ro);
              if (e) {
                const t = e.value.length;
                setTimeout(() => {
                  e.value.length > t && (e.value = e.value.slice(0, t));
                });
              }
            }
          });
        const s = null !== (t = e.name) && void 0 !== t ? t : "oda-chat";
        this.Ro = `.${s}-user-input`;
      }
      add(e, t, s = !0) {
        this.Lo && (this.No(), (this.Lo = !1));
        const i = e.toUpperCase(),
          o = isNaN(i) ? `Key${i}` : `Digit${i}`;
        this.Po.set(o, { check: s, elem: t }),
          t.setAttribute("aria-keyshortcuts", `Alt+${i}`);
      }
      setWidget(e) {
        this.Ho = e;
      }
      remove() {
        document.removeEventListener(dr, this.jo);
      }
      No() {
        document.addEventListener(dr, this.jo);
      }
      Fo(e) {
        let t = !1;
        const s = this.Po.get(e),
          i = s && s.elem;
        return (
          i &&
            P(s.check ? this.Ho : i) &&
            !i.disabled &&
            (i.focus(), i.click(), (t = !0)),
          t
        );
      }
    }
    const gr = (e) =>
        e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey && !e.repeat,
      mr = {
        SESSION: "sessionStorage",
        LOCAL: "localStorage",
        CUSTOM: "custom",
      },
      br = {
        CLASSIC: "classic",
        DEFAULT: "default",
        REDWOOD_DARK: "redwood-dark",
      },
      fr = "audio",
      wr = "file",
      vr = "location",
      xr = "visual";
    class kr {
      constructor(e) {
        (this.getItem = (e) => (
          !this.Uo[e] && this.Vo && (this.Uo[e] = this.Bo.getItem(e)),
          this.Uo[e]
        )),
          (this.setItem = (e, t) => {
            this.Vo
              ? (this.Bo.setItem(e, t), delete this.Uo[e])
              : (this.Uo[e] = t);
          }),
          (this.removeItem = (e) => {
            this.Vo && this.Bo.removeItem(e), delete this.Uo[e];
          }),
          (this.Uo = {}),
          ya(e) ? ((this.Vo = !0), (this.Bo = window[e])) : (this.Vo = !1);
      }
    }
    const yr = { ARROW_DOWN: "ArrowDown", ARROW_UP: "ArrowUp", ENTER: "Enter" },
      zr = "keyboard",
      $r = "voice",
      Cr = {
        AUDIO:
          ".aac, .amr, .m4a, .mp3, .mp4a, .mpga, .oga, .ogg, .wav, audio/*",
        FILE: ".7z, .csv, .doc, .docx, .eml, .ics, .key, .log, .msg, .neon, .numbers, .odt, .pages, .pdf, .pps, .ppsx, .ppt, .pptx, .rtf, .txt, .vcf, .xls, .xlsx, .xml, .yml, .yaml, application/msword, application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        IMAGE:
          ".gif, .jfif, .jpeg, .jpg, .png, .svg, .tif, .tiff, .webp, image/*",
        VIDEO:
          ".3g2, .3gp, .avi, .m4v, .mov, .mp4, .mpeg, .mpg, .ogv, .qt, .webm, .wmv, video/*",
        ALL: "",
      };
    Cr.ALL = `${Cr.AUDIO},${Cr.FILE},${Cr.IMAGE},${Cr.VIDEO}`;
    const Sr = setTimeout;
    class Ir extends Pi {
      constructor(e, t, s, i, o, r, a, n, c, h, l) {
        super(),
          (this.fs = e),
          (this.Wo = t),
          (this.qo = s),
          (this.Vs = i),
          (this.Zo = o),
          (this.Go = r),
          (this.Yo = a),
          (this.Jo = n),
          (this.Ko = c),
          (this.Ho = h),
          (this.Xo = l),
          (this.Qo = void 0),
          (this.er = fi),
          (this.tr = !1),
          (this.sr = []),
          (this.ir = !1),
          (this.rr = !1),
          (this.nr = !1),
          (this.cr = !0),
          (this.hr = () => {
            var e, t;
            const s = this.lr;
            if (!(null == s ? void 0 : s.nodeType)) return;
            const i = this.fs,
              o = "none",
              r =
                (null ===
                  (t =
                    null === (e = this.pr) || void 0 === e
                      ? void 0
                      : e.value) || void 0 === t
                  ? void 0
                  : t.trim().length) > 0;
            this.Qo === zr && (this.Vs.alwaysShowSendButton || r)
              ? i.removeCSSClass(s, o)
              : i.addCSSClass(s, o),
              (s.disabled = this.dr || !r);
          }),
          (this.ur = (e) => {
            var t;
            this.isDisabled() ||
              (this.Vs.enableAutocomplete &&
                this.gr.isOpen() &&
                this.gr.handleKeyboardEvent(e)) ||
              (e.key === F &&
                !e.shiftKey &&
                (null === (t = this.pr.value) || void 0 === t
                  ? void 0
                  : t.trim().length) > 0 &&
                (e.preventDefault(), this.lr.click()));
          }),
          (this.mr = _n((e) => {
            this.Ko.trigger(ui.TYPING, e);
          }, 1e3)),
          (this.br = _n((e) => {
            this.Jo("RESPONDING", this.Vs.enableAgentSneakPreview ? e : "...");
          }, this.Vs.typingStatusInterval * wi)),
          (this.wr = (e) => {
            var t;
            if ((this.hr(), this.isDisabled()))
              return this.vr(), void this.kr();
            if (e.isComposing) return;
            const s =
              null === (t = this.pr.value) || void 0 === t ? void 0 : t.trim();
            this.mr(!0),
              this.Vs.enableSendTypingStatus &&
                (s ? this.br(s) : this.Jo("LISTENING")),
              clearTimeout(this.yr),
              (this.yr = Sr(() => {
                this.mr(!1),
                  this.Vs.enableSendTypingStatus && this.Jo("LISTENING");
              }, this.Vs.typingStatusInterval * wi)),
              this.Vs.enableAutocomplete &&
                (e.code === Z &&
                  ((this.zr = void 0),
                  this.vr(),
                  this.kr(),
                  clearTimeout(this.$r)),
                this.Cr().includes(e.code) ||
                  (s.length >= 3
                    ? this.zr !== s &&
                      ((this.zr = s), clearTimeout(this.$r), this.Sr())
                    : ((this.zr = void 0), this.kr(), clearTimeout(this.$r))));
          }),
          (this.Ir = () => {
            if (!this.Vs.searchBarMode) {
              this.pr.style.height = null;
              const e = 0.6 * this.Ho.chatWidgetDiv.clientHeight,
                t = this.pr.scrollHeight;
              this.pr.style.height = `${Math.min(e, t)}px`;
            }
          }),
          (this.Xi = i.name),
          (this.Mr = i.i18n),
          (this.Tr = i.icons),
          (this.gi = Object.assign(
            Object.assign({}, this.Mr.en),
            this.Mr[i.locale]
          )),
          (this.cr = !(S() || I())),
          (this.Ar = `${this.Xi}-share-button`);
      }
      render() {
        this.element = this._r();
        const e = this.Er();
        if (this.Vs.enableSpeech) {
          const t = this.Or();
          this.Vs.searchBarMode
            ? e.appendChild(t)
            : this.element.appendChild(t);
        }
        this.element.appendChild(e),
          this.setInputMode(zr),
          this.disable(),
          window.addEventListener(
            "resize",
            An(() => {
              this.Ir();
            }, 100)
          );
      }
      setInputMode(e) {
        e !== this.Qo &&
          (this.Vs.enableSpeech
            ? ((this.Qo = e), this.Qo === zr ? this.Pr() : this.Lr())
            : ((this.Qo = zr), this.Pr()));
      }
      getInputMode() {
        return this.Qo;
      }
      setUserInputText(e) {
        this.pr &&
          ((this.pr.value = e),
          this.pr.setSelectionRange(e.length, e.length),
          this.focusTextArea(),
          this.hr());
      }
      getUserInputText() {
        return this.pr.value;
      }
      setUserInputPlaceholder(e) {
        this.pr && (this.Qo === zr ? this.jr(e) : (this.Fr = e));
      }
      setRecognitionRequested(e) {
        this.nr = e;
      }
      setVoiceRecording(e) {
        this.Vs.enableSpeech &&
          (e && this.nr ? this.setInputMode($r) : e || this.setInputMode(zr));
      }
      updateVisualizer(e, t) {
        this.Qo === $r &&
          ((e, t, s = "#000") => {
            const i = t.height,
              o = t.width,
              r = Math.floor(i / 2);
            let c = a(e, 31);
            c = n(c, i / 255);
            const h = t.getContext("2d");
            if (h) {
              (h.fillStyle = s), h.clearRect(0, 0, o, i), h.save();
              let e = 0;
              c.forEach((t) => {
                const s = Math.ceil(t / 2) + 1;
                h.fillRect(e, r - s, 2, 2 * s), (e += 8);
              }),
                h.save();
            }
          })(e, this.Rr, t);
      }
      focusTextArea() {
        this.cr && ((this.tr = !0), this.pr.focus(), (this.tr = !1)),
          (this.pr.scrollTop = this.pr.scrollHeight);
      }
      isProgrammaticFocus() {
        return this.tr;
      }
      disable(e = !0) {
        const t = this.fs,
          s = "disabled";
        this.Vs.enableAttachment && (this.Nr.disabled = e),
          e
            ? (t.addCSSClass(this.pr, s),
              this.Vs.enableAutocomplete && (this.vr(), this.kr()))
            : t.removeCSSClass(this.pr, s),
          this.Vs.enableSpeech &&
            (this.setInputMode(zr),
            this.disableVoiceModeButton(e, { src: "network" })),
          (this.dr = e),
          this.hr();
      }
      isDisabled() {
        return this.dr;
      }
      disableVoiceModeButton(e, { src: t }) {
        if (this.Vs.enableSpeech) {
          switch (t) {
            case "lang":
              this.ir = e;
              break;
            case "network":
              this.rr = e;
          }
          this.Vs.multiLangChat && (this.ir || this.rr)
            ? (this.Dr.disabled = !0)
            : (this.Dr.disabled = this.rr);
        }
      }
      displaySuggestions(e) {
        if (
          ((this.Hr = e), (this.Ur = e.length > 0), !this.Ur || !this.pr.value)
        )
          return void this.kr();
        const t = this.pr.value.trim().toLowerCase();
        this.gr.display(
          e.slice(0, Math.min(e.length, gi.MAX_SUGGESTIONS_COUNT)),
          t
        );
      }
      getSuggestions() {
        return this.Hr;
      }
      getSuggestionsValid() {
        return this.Ur;
      }
      getSuggestionsList() {
        var e;
        return null === (e = this.gr) || void 0 === e ? void 0 : e.getListbox();
      }
      setLocale(e) {
        (this.gi = e),
          this.Nr &&
            (Tr(this.Nr, e.upload),
            this.Vr.querySelectorAll("li").forEach((e) => {
              const t = e.dataset.value,
                s =
                  this.gi[
                    `share${
                      t.charAt(0).toUpperCase() + t.substring(1).toLowerCase()
                    }`
                  ] ||
                  this.gi[t] ||
                  e;
              e.querySelector("span").innerText = s;
            })),
          this.setUserInputPlaceholder(e.inputPlaceholder),
          this.lr && Tr(this.lr, e.send),
          this.Dr && Tr(this.Dr, e.speak),
          this.Br && Tr(this.Br, e.inputPlaceholder);
      }
      updateInputHeight() {
        this.Ir();
      }
      _r() {
        return this.fs.createDiv(["footer"]);
      }
      Pr() {
        var e;
        const t = this.fs;
        t.removeCSSClass(this.element, "mode-voice"),
          t.addCSSClass(this.element, "mode-keyboard"),
          this.jr(this.Fr),
          (this.pr.disabled = !1),
          this.hr(),
          this.Vs.enableAutocomplete &&
            (null === (e = this.pr.value) || void 0 === e
              ? void 0
              : e.trim().length) >= 3 &&
            this.Sr();
      }
      Lr() {
        const e = this.fs;
        e.removeCSSClass(this.element, "mode-keyboard"),
          e.addCSSClass(this.element, "mode-voice"),
          (this.Fr = this.pr.placeholder),
          this.jr(this.gi.recognitionTextPlaceholder),
          (this.pr.disabled = !0),
          this.hr(),
          this.kr();
      }
      Er() {
        var e;
        const t = this.fs,
          s = t.createDiv(["footer-mode-keyboard", "flex"]),
          i = this.Vs,
          o = null === (e = i.icons) || void 0 === e ? void 0 : e.footerLogo;
        if (
          (o &&
            s.appendChild(
              t.createImageIcon({ icon: o, iconCss: ["footer-logo"] })
            ),
          i.searchBarMode)
        ) {
          const e = t.createDiv(["input-start-slot"]);
          (e.id = `${this.Xi}-input-start-slot`), s.appendChild(e);
        }
        this.Wr(s);
        const r = t.createDiv(["footer-actions", "flex"]),
          a = this.qr();
        if (
          ((this.lr = a),
          this.Xo("send", a),
          r.appendChild(a),
          i.enableSpeech &&
            ((this.Dr = this.Zr()),
            r.appendChild(this.Dr),
            (this.Br = this.Gr()),
            r.appendChild(this.Br)),
          i.enableAttachment)
        ) {
          const e = this.Yr();
          r.appendChild(e);
        }
        return s.appendChild(r), s;
      }
      Yr() {
        const e = this.fs,
          t = e.createDiv(),
          s = Mr(this.fs, {
            css: ["button-upload", "flex"],
            customIcon: this.Tr.shareMenu,
            defaultIcon: $a,
            title: this.gi.upload,
          });
        s.id = this.Ar;
        const i = e.createElement("input", ["none"]);
        (i.type = "file"),
          (i.tabIndex = -1),
          i.setAttribute("aria-hidden", "true"),
          (this.Jr = i),
          (this.Vr = this.Kr(s));
        const o = e.getMenuButton({
          button: s,
          menuId: this.Vr.id,
          menu: this.Vr,
          widget: this.Vs.searchBarMode
            ? this.Ho.element
            : this.Ho.chatWidgetDiv,
        });
        return (
          Zn(o, "click", () => {
            this.kr();
          }),
          (this.Nr = o),
          this.Xo("shareMenu", o),
          document.addEventListener(
            "deviceready",
            () => {
              const e = globalThis
                ? globalThis.device
                : window
                ? window.device
                : void 0;
              "Android" === (null == e ? void 0 : e.platform) &&
                this.Jr.removeAttribute("accept");
            },
            !1
          ),
          Zn(i, "click", () => (i.value = null)),
          Zn(i, "change", (e) => {
            const t = e.target;
            t.files && t.files.length && this.Xr(t.files[0]);
          }),
          t.appendChild(this.Nr),
          t.appendChild(this.Vr),
          t.appendChild(i),
          t
        );
      }
      Kr(e) {
        return this.fs.getMenu({
          menuId: `${this.Vs.name}-share-menu`,
          menuClassList: ["share-popup-list"],
          buttonId: this.Ar,
          menuItems: this.Qr(),
          menuButton: e,
        });
      }
      Qr() {
        const e = this.fs,
          t = this.Tr,
          s = this.gi,
          i = this.Jr,
          o = `${this.Xi}-share-`;
        let r = this.Vs.shareMenuItems;
        const a = [],
          n = [fr, wr, vr, xr],
          c = new Set();
        if (
          (((null == r ? void 0 : r.length) &&
            !r.every(
              (e) => "string" == typeof e && !n.includes(e.toLowerCase())
            )) ||
            (r = n),
          r.forEach((e) => {
            "string" == typeof e && c.add(e.toLowerCase());
          }),
          c.has(xr))
        ) {
          const r = `${o}visual`,
            n = t.shareMenuVisual || Ka,
            c = e.createListItem(
              r,
              s.shareVisual,
              "visual",
              n,
              "share-popup-item",
              () => {
                (i.accept = `${Cr.IMAGE},${Cr.VIDEO}`), i.click();
              }
            );
          a.push(c), this.Xo("shareMenuVisual", c);
        }
        if (c.has(fr)) {
          const r = `${o}audio`,
            n = t.shareMenuAudio || Ga,
            c = e.createListItem(
              r,
              s.shareAudio,
              "audio",
              n,
              "share-popup-item",
              () => {
                (i.accept = Cr.AUDIO), i.click();
              }
            );
          a.push(c), this.Xo("shareMenuAudio", c);
        }
        if (c.has(wr)) {
          const r = `${o}file`,
            n = t.shareMenuFile || Ya,
            c = e.createListItem(
              r,
              s.shareFile,
              "file",
              n,
              "share-popup-item",
              () => {
                (i.accept = Cr.FILE), i.click();
              }
            );
          a.push(c), this.Xo("shareMenuFile", c);
        }
        if (c.has(vr)) {
          const i = `${o}location`,
            r = t.shareMenuLocation || Ja,
            n = e.createListItem(
              i,
              s.shareLocation,
              "location",
              r,
              "share-popup-item",
              () => this.Yo()
            );
          a.push(n), this.Xo("shareMenuLocation", n);
        }
        const h = t.shareMenuFile || Ya;
        return (
          this.Vs.shareMenuItems
            .filter((e) => "string" != typeof e && "string" == typeof e.type)
            .forEach((t) => {
              const o = t.type.toLowerCase(),
                r = `share_${o.includes("*") ? "all" : o.replace(/ /g, "_")}`,
                n = `${this.Xi}-${r}`,
                c = s[r] || this.Mr.en[r];
              let l = t.label;
              c ? (l = c) : (this.Mr.en[r] = l);
              const p = t.icon || h,
                d =
                  t.maxSize && t.maxSize >= 1
                    ? Math.min(t.maxSize * bi, fi)
                    : fi;
              let u = "";
              "wcfs_*" !== o &&
                (u =
                  o.includes("*") && "wcfs_*" !== o
                    ? Cr.ALL
                    : o
                        .split(" ")
                        .map((e) => `.${e} `)
                        .join(",")),
                a.push(
                  e.createListItem(n, l, r, p, "share-popup-item", () => {
                    (this.er = d), (i.accept = u), i.click();
                  })
                );
            }),
          a
        );
      }
      Wr(e) {
        const t = this.fs;
        this.pr = this.ea();
        const s = t.createLabel(["hidden"]);
        (s.id = `${this.pr.id}-label`),
          (s.htmlFor = this.pr.id),
          (this.ta = s),
          this.jr(this.Fr),
          e.append(s, this.pr),
          this.Vs.enableAutocomplete &&
            ((this.gr = new _i(
              this.pr,
              `${this.Xi}-suggestions-list`,
              this.fs
            )),
            e.append(this.gr.getListbox()));
      }
      ea() {
        const e = ["user-input"];
        this.Vs.enableSpeech && e.push("user-input-inline-send");
        const t = this.fs.createElement("textarea", e, !0);
        return (
          t.setAttribute("enterkeyhint", "send"),
          (t.id = `${this.Xi}-user-text-input`),
          (this.Fr = this.gi.inputPlaceholder),
          (t.rows = 1),
          Zn(t, "keydown", this.ur),
          Zn(t, "keyup", this.wr),
          Zn(t, "input", () => {
            const e = t.value;
            (this.Ho.speechFinalResult = this.Ho.speechFinalResult || {
              speechId: "",
              text: "",
            }),
              (this.Ho.speechFinalResult.text = e),
              this.Ir();
          }),
          Zn(t, "paste", () => {
            this.dr || Sr(this.hr);
          }),
          this.sa(t),
          this.Xo("input", t),
          t
        );
      }
      jr(e) {
        (this.pr.placeholder = e), (this.ta.innerText = e);
      }
      sa(e) {
        const t = Object.getOwnPropertyDescriptor(
          HTMLTextAreaElement.prototype,
          "value"
        );
        Object.defineProperty(e, "value", {
          set: (s) => {
            t.set.call(e, s), this.hr(), this.Ir();
          },
          get: t.get,
        });
      }
      qr() {
        const e = Mr(this.fs, {
          css: ["button-send"],
          customIcon: this.Tr.send,
          defaultIcon: Za,
          title: this.gi.send,
        });
        return (
          (e.disabled = !0),
          (e.onclick = () => {
            var e;
            this.ia() ||
              ((this.zr = void 0),
              (this.pr.value =
                null === (e = this.pr) || void 0 === e
                  ? void 0
                  : e.value.trim()),
              this.Vs.enableAutocomplete && (this.vr(), this.kr()),
              this.oa());
          }),
          e
        );
      }
      Zr() {
        const e = Mr(this.fs, {
          css: ["button-switch-voice"],
          customIcon: this.Tr.mic,
          defaultIcon: Ba,
          title: this.gi.speak,
        });
        return (
          (e.onclick = () => {
            this.Go(!0), (this.nr = !0);
          }),
          this.Xo("mic", e),
          e
        );
      }
      Or() {
        const e = this.fs,
          t = e.createDiv(["footer-mode-voice", "flex"]),
          s = e.createDiv(["footer-visualizer-wrapper"]);
        return (
          (this.Rr = e.createElement("canvas")),
          (this.Rr.width = 244),
          (this.Rr.height = 32),
          s.appendChild(this.Rr),
          t.appendChild(s),
          t
        );
      }
      Gr() {
        const e = Mr(this.fs, {
          css: ["button-switch-kbd"],
          customIcon: this.Tr.keyboard,
          defaultIcon: Da,
          title: this.gi.inputPlaceholder,
        });
        return (
          (e.onclick = () => {
            (this.nr = !1), this.Go(!1);
          }),
          this.Xo("keyboard", e),
          e
        );
      }
      ia() {
        return !this.pr || 0 === this.pr.value.trim().length;
      }
      oa() {
        this.Wo(this.pr.value),
          (this.pr.value = ""),
          (this.pr.innerText = ""),
          Sr(this.Ir);
      }
      Xr(e) {
        const t = this.er;
        (this.er = fi), this.qo(e, { maxSize: t }), (this.Jr.value = "");
      }
      ra() {
        this.Zo(this.pr.value.trim()).catch(() => {});
      }
      kr() {
        this.gr && this.gr.isOpen() && this.gr.hide();
      }
      Sr() {
        this.$r = Sr(() => {
          this.ra();
        }, 300);
      }
      vr() {
        (this.Hr = null), (this.Ur = !1);
      }
      Cr() {
        if (!this.sr.length)
          for (const e of Object.keys(yr)) this.sr.push(yr[e]);
        return this.sr;
      }
    }
    function Mr(e, { css: t, customIcon: s, defaultIcon: i, title: o }) {
      const r = s || i;
      return e.createIconButton({
        css: ["footer-button", "flex"].concat(t),
        icon: r,
        iconCss: [],
        title: o,
      });
    }
    function Tr(e, t) {
      e.title = t;
    }
    const Ar = "end-conversation",
      _r = "collapse",
      Er = "clear",
      Or = "tts",
      Pr = "none";
    class Lr extends Pi {
      constructor(e, t, s, i, o, r, a, n, c) {
        super(),
          (this.Vs = e),
          (this.fs = t),
          (this.le = s),
          (this.aa = i),
          (this.na = o),
          (this.ca = r),
          (this.ha = a),
          (this.Xo = n),
          (this.Ho = c),
          (this.di = new ar("ChatHeaderComponent")),
          (this.la = []),
          (this.pa = []),
          (this.Xi = e.name),
          (this.gi = Object.assign(
            Object.assign({}, this.Vs.i18n.en),
            this.Vs.i18n[e.locale]
          ));
      }
      render() {
        return (
          (this.element = this._r()),
          this.Vs.showConnectionStatus &&
            ((this.da = (e) => this.ua(e)), this.ca.on(_t.State, this.da)),
          this.disable(),
          this.element
        );
      }
      addLanguageSelect(e) {
        const t = !(!this.pa || !this.pa.length);
        (this.ga = e.render(t)),
          this.Xo("language", this.ga),
          this.ga &&
            (t ? this.ma.appendChild(this.ga) : this.ba.prepend(this.ga));
      }
      closeWidgetPopup() {
        this.le();
      }
      clearHistory() {
        this.aa();
      }
      showTTSButton(e) {
        const t = this.fa(Or);
        t && (t.style.display = e ? "flex" : Pr);
      }
      disableTTSButton(e) {
        const t = this.fa(Or);
        if (t) {
          const s = this.fs;
          if ("LI" === t.tagName) {
            const i = "disable";
            e
              ? (s.addCSSClass(t, i), (t.ariaDisabled = "true"))
              : (s.removeCSSClass(t, i), (t.ariaDisabled = "false"));
          } else t.disabled = e;
        }
      }
      setLocale(e) {
        var t;
        const s = this.fs,
          i = this.ga;
        this.gi = e;
        const o = e.chatTitle;
        o && (this.ei.innerText = o);
        const r = e.chatSubtitle;
        r
          ? ((this.wa.innerText = r),
            s.removeCSSClass(this.wa, Pr),
            s.addCSSClass(this.va, Pr))
          : this.Vs.showConnectionStatus
          ? (this.ua(this.xa),
            s.removeCSSClass(this.va, Pr),
            s.addCSSClass(this.wa, Pr))
          : (s.addCSSClass(this.wa, Pr), s.addCSSClass(this.va, Pr)),
          this.ka && jr(this.ka, e.showOptions),
          null === (t = this.la) ||
            void 0 === t ||
            t.forEach((t) => {
              jr(t.element, e[t.title]);
            }),
          i && jr(i.querySelector("button") || i, e.languageSelectDropdown);
      }
      disable(e = !0) {
        if (
          this.Vs.enableEndConversation &&
          !this.Vs.wcfsEnableEndConversationButtonToClose
        )
          for (const t of this.la) t.name === Ar && (t.element.disabled = e);
      }
      addAction(e) {
        this.la.push(e);
      }
      remove() {
        this.ca.off(_t.State, this.da);
      }
      _r() {
        var e;
        const t = this.fs,
          s = this.Vs,
          i = s.icons,
          o = t.createDiv(["header", "flex"]),
          r = t.createDiv(["header-info-wrapper"]),
          a = t.createDiv(["header-actions", "flex"]),
          n = this.gi,
          c = n.chatTitle,
          h = n.chatSubtitle;
        if (!("logo" in i) || i.logo) {
          const e = t.createImageIcon({
            icon: i.logo || Va,
            iconCss: ["logo"],
          });
          o.appendChild(e);
        }
        if (c) {
          const e = t.createTextDiv(["title"]);
          (e.id = `${s.name}-title`),
            (e.innerText = c),
            r.appendChild(e),
            (this.ei = e);
        }
        (this.wa = t.createTextDiv(["subtitle", Pr])),
          r.appendChild(this.wa),
          (this.va = t.createTextDiv(["connection-status", Pr])),
          r.appendChild(this.va),
          h
            ? ((this.wa.innerText = h), t.removeCSSClass(this.wa, Pr))
            : s.showConnectionStatus &&
              (this.ua(this.ca.getState()), t.removeCSSClass(this.va, Pr)),
          o.appendChild(r);
        const l = t.createDiv(["header-gap"]);
        if ((o.appendChild(l), s.customHeaderElementId)) {
          const e = document.getElementById(s.customHeaderElementId);
          if (e) {
            const s = t.createDiv(["header-custom-element"]);
            s.appendChild(e), o.appendChild(s);
          } else
            this.di.error(
              `Could not find element with ID '${s.customHeaderElementId}'. No custom element added to the chat header.`
            );
        }
        if (((this.ba = a), s.enableEndConversation)) {
          const e = i.close || _a;
          this.la.push({
            name: Ar,
            title: "endConversation",
            icon: e,
            clickHandler: this.ha.bind(this),
            order: 10,
          });
        }
        if (!s.embedded) {
          const e = i.collapse || Ea;
          this.la.push({
            name: _r,
            title: "close",
            icon: e,
            clickHandler: this.closeWidgetPopup.bind(this),
            order: 20,
          });
        }
        if (
          (s.enableBotAudioResponse &&
            ((this.ya = !s.initBotAudioMuted),
            this.la.push({
              name: Or,
              title: this.ya ? "audioResponseOn" : "audioResponseOff",
              icon: this.ya ? i.ttsOn || en : i.ttsOff || Qa,
              clickHandler: () => {
                (this.ya = !this.ya), this.za(), this.na(this.ya);
              },
              order: 30,
            })),
          s.enableClearMessage)
        ) {
          const e = i.clearHistory || Aa;
          this.la.push({
            name: Er,
            title: "clear",
            icon: e,
            clickHandler: this.clearHistory.bind(this),
            order: 40,
          });
        }
        return (
          this.la.sort((e, t) => (e.order > t.order ? 1 : -1)),
          null === (e = this.la) ||
            void 0 === e ||
            e.forEach((e, s) => {
              const i = this.Vs.multiLangChat
                ? this.la.length + 1
                : this.la.length;
              if (
                !this.Vs.enableHeaderActionCollapse ||
                (s < 2 && !(i > 2 && 1 === s))
              ) {
                const s = t.createIconButton({
                  css: ["header-button"],
                  icon: e.icon,
                  iconCss: [],
                  title: n[e.title],
                });
                (s.onclick = e.clickHandler),
                  this.$a(e, s),
                  (e.element = s),
                  this.ba.prepend(s);
              } else this.pa.push(e);
            }),
          this.pa && this.pa.length && this.Ca(this.pa),
          o.appendChild(a),
          o
        );
      }
      $a(e, t) {
        switch (((t.id = `${this.Xi}-${e.name}`), e.name)) {
          case Ar:
            this.Xo("close", t);
            break;
          case _r:
          case Or:
            this.Xo(e.name, t);
            break;
          case Er:
            this.Xo("clearHistory", t);
        }
      }
      Ca(e) {
        const t = this.fs,
          s = this.gi,
          i = `${this.Vs.name}-action-menu`,
          o = `${i}-button`,
          r = e.map((e) => {
            const i = t.createListItem(
              `action-menu-option-${e.name}`,
              s[e.title],
              e.name,
              e.icon,
              "action-item",
              e.clickHandler
            );
            return this.$a(e, i), (e.element = i), i;
          }),
          a = t.createIconButton({
            css: ["header-button", "button-show-options"],
            icon: La,
            iconCss: [],
            title: s.showOptions,
          }),
          n = t.getMenu({
            menuId: i,
            menuClassList: ["action-menu"],
            menuItems: r,
            buttonId: o,
            menuButton: a,
          }),
          c = t.getMenuButton({
            button: a,
            menuId: i,
            menu: n,
            widget: this.Ho.chatWidgetDiv,
          });
        this.ba.prepend(n), this.ba.prepend(c), (this.ka = c), (this.ma = n);
      }
      Sa(e) {
        for (const t of this.la) if (t.name === e) return t;
        return null;
      }
      fa(e) {
        var t;
        return null === (t = this.Sa(e)) || void 0 === t ? void 0 : t.element;
      }
      za() {
        const e = this.Vs.icons,
          t = this.Sa(Or);
        (t.title = this.ya ? "audioResponseOn" : "audioResponseOff"),
          (t.icon = this.ya ? e.ttsOn || en : e.ttsOff || Qa),
          this.updateHeaderAction(Or);
      }
      updateHeaderAction(e) {
        const t = this.fs,
          s = this.gi,
          i = this.Sa(e),
          o = this.fa(e);
        if (o) {
          o.innerHTML = "";
          const e = s[i.title],
            r = i.icon,
            a = "LI" === o.tagName,
            n = t.createImageIcon({
              icon: r,
              iconCss: [a ? "icon" : "", "action-item-icon"],
            });
          if (a) {
            o.appendChild(n);
            const s = t.createTextSpan([
              "text",
              "action-item-text",
              "ellipsis",
            ]);
            (s.innerText = e), o.appendChild(s);
          } else o.appendChild(n), (o.title = e);
        }
      }
      ua(e) {
        const t = this.fs,
          a = "connecting",
          n = "connected",
          c = "disconnected",
          h = this.va,
          l = this.gi;
        switch (((this.xa = e), e)) {
          case i:
            (h.innerText = l.connected),
              t.removeCSSClass(h, a, c),
              t.addCSSClass(h, n);
            break;
          case r:
            (h.innerText = l.disconnected),
              t.removeCSSClass(h, a, n),
              t.addCSSClass(h, c);
            break;
          case o:
            (h.innerText = l.closing),
              t.removeCSSClass(h, n, c),
              t.addCSSClass(h, a);
            break;
          case s:
            (h.innerText = l.connecting),
              t.removeCSSClass(h, n, c),
              t.addCSSClass(h, a);
        }
      }
    }
    function jr(e, t) {
      if ("LI" === e.tagName) {
        const s = e.querySelector("span");
        s && (s.innerText = t);
      } else e.title = t;
    }
    class Fr extends Pi {
      constructor(e) {
        super(), (this.element = e.createDiv(["conversation"]));
      }
      render() {}
    }
    class Rr {
      constructor(e, t, s) {
        let i, o;
        if (
          ((this.ae = t),
          (this.Ho = s),
          (this.di = new ar("MultiLangChatComponent")),
          (this.Ia = !0),
          (this.Ma = !0),
          (this.Ta = !1),
          (this.Aa = {}),
          (this._a = {}),
          (this.Ea = []),
          (this.ca = t.webCore),
          (this.Vs = t.settings),
          (this.gi = Object.assign(
            Object.assign({}, this.Vs.i18n.en),
            this.Vs.i18n[this.Vs.locale]
          )),
          (this.Xi = t.settings.name),
          e &&
            ((this.Oa = Object.assign(Object.assign({}, e), {
              supportedLangs: e.supportedLangs ? [...e.supportedLangs] : [],
            })),
            (i = this.Oa.supportedLangs),
            (o = this.Oa.primary),
            "string" == typeof o && (this.Oa.primary = o.toLowerCase())),
          i && i.length)
        )
          if (
            (i.forEach((e) => {
              e.lang = e.lang.toLowerCase();
            }),
            i.length > 1
              ? (i.unshift({ lang: "und", label: this.gi.language_detect }),
                this.Oa.primary || (this.Oa.primary = null))
              : (this.Oa.primary = i[0].lang),
            (this.Ea = i.map((e) => e.lang)),
            this.Vs.enableBotAudioResponse)
          ) {
            const e = t.synthesisVoices;
            if (e && e.length) {
              const t = {};
              i
                .filter((e) => e.lang && "und" !== e.lang)
                .forEach((s) => {
                  const i = e.filter((e) => e.lang.includes(s.lang));
                  i.push({ lang: s.lang }), (t[s.lang] = i);
                }),
                (this._a = t);
            } else
              new Set(this.Ea.filter((e) => "und" !== e)).forEach((e) => {
                this._a[e] = [{ lang: e, name: e }];
              });
          } else this.Pa = () => {};
        if (this.Vs.enableSpeech) {
          const e = {};
          Object.values(we).forEach((t) => {
            (e[t.substring(0, 2)] = t), (e[t] = t);
          }),
            Dr(we.EN_GB, e),
            Dr(we.EN_AU, e),
            Dr(we.EN_IN, e),
            (this.Aa = e);
        } else this.La = () => {};
      }
      render(e) {
        const t = this.ae.util,
          s = this.Xi,
          i = "language-selection",
          o = `${s}-${i}-button`,
          r = `${s}-${i}-menu`,
          a = this.Oa;
        let n;
        if (
          ((this.Ta = e),
          !(a && a.supportedLangs && a.supportedLangs.length >= 2))
        )
          return null;
        if (!this.ja) {
          const s = this.Vs.icons.language || Ha,
            c = t.createIconButton({
              css: ["header-button", "button-lang"],
              icon: s,
              iconCss: [],
              title: this.gi.languageSelectDropdown,
            }),
            h = t.createListItem(
              "action-menu-option-lang",
              this.gi.languageSelectDropdown,
              "lang",
              s,
              "action-item",
              null,
              !0
            ),
            l = a.supportedLangs.map((e) => {
              var s;
              const { lang: o, label: r } = e,
                n = "und" === o && a.primary ? a.primary : o,
                c = `language_${"und" === o ? "detect" : o}`,
                h =
                  (null === (s = this.Vs.i18n[n]) || void 0 === s
                    ? void 0
                    : s[c]) ||
                  r ||
                  o;
              return t.createListItem(
                `${i}-option-${o}`,
                h,
                o,
                "",
                `${i}-option`,
                (e) => {
                  let t = e.target;
                  "LI" !== t.tagName && (t = t.parentElement);
                  const s = t.dataset.value;
                  this.Fa(s);
                }
              );
            }),
            p = t.getMenu({
              menuId: r,
              menuClassList: [`${i}-menu`],
              menuItems: l,
              buttonId: o,
              menuButton: e ? h : c,
            });
          if (e) {
            n = t.getMenuButton({
              button: h,
              menuId: r,
              menu: p,
              widget: this.Ho.chatWidgetDiv,
            });
            const e = t.createDiv(["arrow-icon"]),
              s = t.createImageIcon({ icon: ja });
            e.appendChild(s), n.appendChild(e);
            this.ae.chatWidget.chatWidgetDiv
              .querySelector(`ul.${this.Xi}-action-menu`)
              .insertAdjacentElement("afterend", p);
          } else {
            n = t.createDiv();
            const e = t.getMenuButton({
              button: c,
              menuId: r,
              menu: p,
              widget: this.Ho.chatWidgetDiv,
            });
            n.appendChild(e), n.appendChild(p), (c.id = o);
          }
          this.disableComponent(!1);
        }
        return (this.ja = n), n;
      }
      setLocale(e) {
        this.ja &&
          ((this.gi = e),
          this.Oa.supportedLangs.forEach((t) => {
            const { lang: s, label: i } = t,
              o = `language_${"und" === s ? "detect" : s}`,
              r = document.getElementById(`language-selection-option-${s}`);
            if (!r) return;
            const a = e[o] || i || s;
            r.title = a;
          }));
      }
      setTag(e, t = !0) {
        let s = "";
        null !== e && (s = e.toLowerCase()),
          this.Ea.length && (s = this.Ea.includes(s) ? s : null),
          this.Fa(s, t);
      }
      disableComponent(e) {
        if (this.ja) {
          const t = this.ae.util,
            s = this.ja;
          if (this.Ta) {
            const i = "disable";
            e ? t.addCSSClass(s, i) : t.removeCSSClass(s, i);
          } else s.querySelector("button").disabled = e;
        }
      }
      Fa(e, t = !0) {
        let s = e;
        (this.gi = this.Vs.i18n[s]),
          this.Ra !== s &&
            ((this.Ra = s), this.ae.eventDispatcher.trigger(ui.CHAT_LANG, s)),
          this.ja && this.Na(s),
          "und" === s && (s = null),
          t && (this.Da(s), this.ae.storageService.setItem(Nr(this.Vs), s)),
          this.Pa(s),
          this.La(s),
          this.ae.chatWidget.onLanguageUpdate(s, t);
      }
      Da(e) {
        if (this.ca.isConnected()) {
          const t = { profile: { languageTag: e } };
          e || (t.profile.locale = e);
          const s = this.Vs.sdkMetadata
            ? Object.assign({ version: mi }, this.Vs.sdkMetadata)
            : { version: mi };
          this.ca
            .updateUser(t, { sdkMetadata: s })
            .catch((e) =>
              this.di.warn("[updateProfile] Failed to update user profile:", e)
            );
        }
      }
      Pa(e) {
        const t = this.ae.chatWidget;
        if (e) {
          if (
            (this.Ia || (t.enableSpeechSynthesisService(!0), (this.Ia = !0)),
            this.Vs.enableBotAudioResponse)
          ) {
            const t = this._a[e];
            this.ca.setTTSVoice(t).catch((e) => {
              this.di.info(`Failed to set TTS voice for '${t[0].lang}'. ${e}`),
                this.Pa(null);
            });
          }
        } else
          (this.Ia = !1),
            this.Vs.enableBotAudioResponse && this.ca.cancelTTS(),
            t.enableSpeechSynthesisService(!1);
      }
      La(e) {
        const t = this.ae,
          s = this.Aa[e],
          i = t.chatWidget;
        s
          ? (this.Ma || (i.setVoiceRecognitionService(!0), (this.Ma = !0)),
            this.ca.setRecognitionLocale(s))
          : ((this.Ma = !1),
            this.ca.stopRecognition(),
            this.ca.setRecognitionLocale(null),
            i.setVoiceRecognitionService(!1));
      }
      Na(e) {
        const t = this.ae.util,
          s = e || "und",
          i = document.getElementById(`${this.Xi}-language-selection-menu`),
          o = "active";
        if (i) {
          const e = i.querySelector(`li.${this.Xi}-${o}`);
          e && t.removeCSSClass(e, o);
          const r = i.querySelector(`[data-value="${s}"]`);
          r && t.addCSSClass(r, o);
        }
      }
      initLanguage() {
        const { primary: e } = this.Oa || {},
          t = this.ae.storageService.getItem(Nr(this.Vs));
        let s = e;
        t && (s = "null" === t ? null : t), void 0 !== s && this.setTag(s);
      }
    }
    function Nr(e) {
      return `${e.name}-${e.channelId}-${e.userId}`;
    }
    function Dr(e, t) {
      xa() === e && (t[e.substring(0, 2)] = e);
    }
    class Hr extends Pi {
      constructor(e) {
        super(),
          (this.ae = e),
          (this.di = new ar("CancelResponseComponent")),
          (this.Ha = !1),
          (this.Ua = () => {
            this.ae.onClick(), this.hide();
          }),
          this.render();
      }
      show() {
        if (!this.Ha) {
          this.Ha = !0;
          try {
            this.appendToElement(this.ae.parent);
          } catch (e) {
            this.di.debug("No parent to add cancel response button");
          }
        }
      }
      hide() {
        if (!this.Ha) return;
        this.Ha = !1;
        const { domUtil: e } = this.ae,
          t = this.element;
        e.addCSSClass(t, Vr),
          setTimeout(() => {
            e.removeCSSClass(t, Vr), this.remove();
          }, Ur),
          this.ae.onHide();
      }
      isVisible() {
        return this.Ha;
      }
      render() {
        const { domUtil: e, i18n: t } = this.ae;
        if (this.element) return void (this.element.title = t.cancelResponse);
        const s = "cancel-response-button",
          i = e.createIconButton({
            css: [s],
            icon: un,
            iconCss: [`${s}-icon`],
            title: t.cancelResponse,
          });
        Zn(i, "click", this.Ua), (this.element = i);
      }
      setLocale(e) {
        (this.ae.i18n = e), this.render();
      }
    }
    const Ur = 210,
      Vr = "hide",
      Br = [
        "no-referrer",
        "no-referrer-when-downgrade",
        "origin",
        "origin-when-cross-origin",
        "same-origin",
        "strict-origin",
        "strict-origin-when-cross-origin",
        "unsafe-url",
      ],
      Wr = [
        "allow-downloads-without-user-activation",
        "allow-downloads",
        "allow-forms",
        "allow-modals",
        "allow-orientation-lock",
        "allow-pointer-lock",
        "allow-popups",
        "allow-popups-to-escape-sandbox",
        "allow-presentation",
        "allow-same-origin",
        "allow-scripts",
        "allow-storage-access-by-user-activation",
        "allow-top-navigation",
        "allow-top-navigation-by-user-activation",
      ],
      qr = "none",
      Zr = "webview-container",
      Gr = `${Zr}-open`,
      Yr = `${Zr}-close`;
    class Jr {
      constructor(e, t, s) {
        (this.fs = t),
          (this.Vs = s),
          (this.Va = 0.8),
          (this.Xt = {
            closeButtonIcon: _a,
            closeButtonType: "icon",
            errorInfoBar: !0,
            referrerPolicy: "no-referrer-when-downgrade",
            sandbox: [],
            size: "tall",
          }),
          (this.Ba = !1),
          (this.Wa = !1),
          this.setProps(e || {}),
          (this.Xi = s.name);
      }
      setProps(e) {
        Array.isArray(e.sandbox) &&
          e.sandbox.length &&
          (e.sandbox = e.sandbox
            .map((e) => e.toLowerCase())
            .filter((e) => Wr.includes(e)));
        const t = Object.assign(Object.assign({}, this.Xt), e);
        var s;
        t.closeButtonIcon || (t.closeButtonIcon = this.Xt.closeButtonIcon),
          t.closeButtonType || (t.closeButtonType = "icon"),
          t.size || (t.size = "tall"),
          (s = t.referrerPolicy),
          Br.includes(null == s ? void 0 : s.toLowerCase()) ||
            (t.referrerPolicy = "no-referrer-when-downgrade"),
          "full" === t.size && (this.Va = 1),
          (this.Xt = t),
          (this.Ba = !1),
          (this.Wa = !1);
      }
      open(e) {
        if (this.ja) {
          const t = this.fs,
            s = 100;
          (this.ja.style.height = s * this.Va + "%"),
            t.removeCSSClass(this.ja, Yr, qr),
            t.addCSSClass(this.ja, Gr),
            this.ja.insertBefore(this.qa, this.Za),
            (this.Za.onload = () => {
              this.qa.remove(), t.removeCSSClass(this.Za, qr);
            }),
            this.Xt.title || (this.ei.textContent = e),
            this.Xt.errorInfoBar &&
              setTimeout(() => {
                this.Ba &&
                  !this.Wa &&
                  ((this.Ga = this.Ya()),
                  e && (this.Ja.href = e),
                  t.removeCSSClass(this.Ga, qr),
                  this.ja.appendChild(this.Ga),
                  (this.Wa = !0));
              }, 1e3),
            (this.Ba = !0);
        }
      }
      close() {
        const e = this.fs;
        (this.Ba = !1),
          e.removeCSSClass(this.ja, Gr),
          e.addCSSClass(this.ja, Yr),
          this.Ka(),
          this.Za.setAttribute("src", ""),
          setTimeout(() => {
            e.addCSSClass(this.ja, qr), e.removeCSSClass(this.Za, qr);
          }, 400);
      }
      render() {
        const e = this.fs,
          t = this.Xt;
        return (
          (this.ja = e.createDiv(["webview-container"])),
          (this.Xa = e.createDiv(["header", "webview-header", "flex"])),
          (this.ei = e.createTextDiv(["title", "webview-title", "ellipsis"])),
          (this.Qa = e.createIconButton({
            css: ["header-button", "webview-button-close"],
            icon: t.closeButtonIcon,
            iconCss: [],
            title: t.closeButtonLabel,
          })),
          (this.Qa.id = `${this.Xi}-webview-button-close`),
          (this.qa = this.tn()),
          (this.Za = e.createElement("iframe", ["iframe", "webview"])),
          (this.Za.name = `${this.Vs.name}-webview`),
          (this.Za.title = t.accessibilityTitle),
          t.title && (this.ei.textContent = t.title),
          "label" === t.closeButtonType
            ? (this.Qa.classList.add(`${this.Xi}-label-only`),
              this.Qa.appendChild(document.createTextNode(t.closeButtonLabel)))
            : "iconWithLabel" === t.closeButtonType &&
              (this.Qa.classList.add(`${this.Xi}-with-label`),
              this.Qa.appendChild(document.createTextNode(t.closeButtonLabel))),
          this.Za.setAttribute("referrerpolicy", t.referrerPolicy),
          this.Xt.sandbox.length &&
            this.Xt.sandbox.forEach((e) => {
              this.Za.sandbox.add(e);
            }),
          e.addCSSClass(this.ja, qr),
          (this.Qa.onclick = () => {
            this.close();
          }),
          this.Xa.appendChild(this.ei),
          this.Xa.appendChild(this.Qa),
          this.ja.appendChild(this.Xa),
          this.ja.appendChild(this.Za),
          this.ja
        );
      }
      tn() {
        return new Uo(this.fs).render();
      }
      Ya() {
        const e = this.fs,
          t = e.createDiv(["webview-error", "flex"]);
        (this.sn = e.createDiv(["webview-error-text"])),
          t.appendChild(this.sn),
          this.rn(this.Xt.errorInfoText);
        const s = e.createIconButton({
          css: ["webview-error-button-close"],
          icon: this.Xt.closeButtonIcon,
          iconCss: [],
          title: this.Xt.errorInfoDismissLabel,
        });
        return (s.onclick = this.Ka.bind(this)), t.appendChild(s), t;
      }
      rn(e) {
        var t;
        const s = this.fs,
          i =
            ((o = e),
            $n.forEach((e) => {
              o = o.replace(b(e.match), e.replace);
            }),
            o);
        var o;
        let r;
        const a = /\{0\}(.*)\{\/0\}/g,
          n = null === (t = a.exec(i)) || void 0 === t ? void 0 : t[1];
        if (n) {
          const e = s.createAnchor("", n, ["webview-alt-link"]);
          r = i.replace(b(a), e.outerHTML);
        } else r = s.createAnchor("", i, ["webview-alt-link"]).outerHTML;
        (this.sn.innerHTML = r), (this.Ja = this.sn.querySelector("a"));
      }
      Ka() {
        const e = this.fs;
        this.Wa &&
          (e.addCSSClass(this.Ga, qr),
          setTimeout(() => {
            this.ja.removeChild(this.Ga), (this.Wa = !1);
          }, 600));
      }
    }
    const Kr = "none";
    class Xr extends Pi {
      constructor(e) {
        super(),
          (this.ae = e),
          (this.di = new ar("ScrollDownComponent")),
          (this.Ha = !1),
          (this.an = () => {
            this.nn.scrollHeight > this.nn.offsetHeight &&
            this.nn.scrollTop + this.nn.offsetHeight <
              this.nn.scrollHeight - this.element.offsetHeight
              ? this.cn()
              : this.hn();
          }),
          (this.Ua = () => {
            this.nn.scrollTop =
              this.nn.scrollTop +
              this.nn.offsetHeight -
              this.element.offsetHeight;
          }),
          (this.nn = e.parent),
          (this.ln = new ResizeObserver(this.an)),
          (this.pn = e.domUtil),
          this.render();
      }
      render() {
        if (this.element) return;
        const e = this.ae.i18n,
          t = this.pn.createIconButton({
            css: [],
            icon: gn,
            iconCss: [],
            title: e.scrollDown,
          }),
          s = this.pn.createDiv(["scroll-down-button-wrapper"]);
        s.appendChild(t),
          Zn(t, "click", this.Ua),
          Zn(this.nn, "scroll", this.an),
          this.ln.observe(this.nn),
          this.ae.content && this.ln.observe(this.ae.content),
          this.pn.addCSSClass(s, Kr),
          (this.element = s);
        try {
          this.appendToElement(this.nn);
        } catch (e) {
          this.di.debug("No parent to add this scroll button");
        }
      }
      cn() {
        this.Ha || ((this.Ha = !0), this.pn.removeCSSClass(this.element, Kr));
      }
      hn() {
        this.Ha && ((this.Ha = !1), this.pn.addCSSClass(this.element, Kr));
      }
    }
    class Qr {
      constructor(e) {
        this.isPinned = !1;
        const { domUtil: t, pinLabel: s, unpinLabel: i } = e,
          { onPin: o, onUnpin: r } = e.pinningEvents,
          a = (e = !0) => {
            this.isPinned
              ? (n(c, s), (this.isPinned = !1), r())
              : (n(h, i),
                (this.buttonElement.title = s),
                (this.isPinned = !0),
                o()),
              e && this.buttonElement.focus();
          },
          n = (e, t) => {
            const s = this.buttonElement.querySelector("svg, img");
            null == s || s.remove(),
              this.buttonElement.append(e),
              (this.buttonElement.title = t);
          };
        this.buttonElement = t.createIconButton({
          css: [],
          icon: mn,
          iconCss: [],
          title: s,
        });
        const c = this.buttonElement.querySelector("svg, img"),
          h = t.createImageIcon({ icon: _a });
        Zn(this.buttonElement, "click", () => a()),
          (this.isPinned = e.isPinned),
          e.isPinned &&
            ((this.isPinned = !1),
            setTimeout(() => {
              a(!1);
            }, 0));
      }
    }
    const ea = "none";
    class ta {
      constructor(e) {
        (this.dn = () => {}),
          (this.un = { isPinned: !1 }),
          (this.setPinningVisibility = (e) => {
            this.isPinned ||
              (e
                ? (this.pn.removeCSSClass(this.gn, ea), (this.isVisible = !0))
                : (this.pn.addCSSClass(this.gn, ea), (this.isVisible = !1)));
          }),
          (this.scrollToTop = () => {
            this.isPinned && (this.mn.scrollTop = 0);
          }),
          (this.bn = () => {
            this.dn(),
              this.fn(!0),
              this.pn.addCSSClass(
                this.mn,
                "search-bar-widget-pinned-wrapper",
                "wrapper"
              ),
              this.pn.addCSSClass(this.wn, "search-bar-widget-pinned-content"),
              this.mn.prepend(this.wn),
              this.mn.prepend(this.gn),
              this.vn();
          }),
          (this.xn = () => {
            this.pn.removeCSSClass(
              this.mn,
              "search-bar-widget-pinned-wrapper",
              "wrapper"
            ),
              this.pn.removeCSSClass(
                this.wn,
                "search-bar-widget-pinned-content"
              ),
              this.kn.prepend(this.wn),
              this.kn.prepend(this.gn),
              this.fn(!1),
              this.yn.focus(),
              this.vn();
          }),
          (this.vn = () => {
            (this.un.isPinned = this.isPinned),
              this.Ko.trigger(ui.CLICK_SEARCH_BAR_PINNING, this.un);
          }),
          (this.fn = (e) => {
            this.wn.childNodes.forEach((t) => {
              e ? this.pn.removeCSSClass(t, ea) : this.pn.addCSSClass(t, ea);
            });
          }),
          (this.isVisible = !0),
          (this.mn = e.targetContainer),
          (this.wn = e.conversationContainer),
          (this.yn = e.footerTextArea),
          (this.kn = e.conversationContainer.parentElement),
          (this.pn = e.domUtil),
          (this.Ko = e.eventDispatcher),
          (this.dn = e.closePopup);
        const { i18n: t, isPinned: s } = e;
        new Xr({
          parent: this.mn,
          content: this.wn,
          i18n: t,
          domUtil: this.pn,
        }),
          (this.zn = new Qr({
            domUtil: this.pn,
            isPinned: s,
            pinLabel: t.pin,
            unpinLabel: t.unpin,
            pinningEvents: { onPin: this.bn, onUnpin: this.xn },
          }));
        (this.gn = this.pn.createDiv(["pin-button-wrapper"])),
          this.gn.appendChild(this.zn.buttonElement),
          this.pn.addCSSClass(this.wn, "search-bar-popup-pinned"),
          this.kn.prepend(this.gn);
      }
      get isPinned() {
        return this.zn.isPinned;
      }
    }
    const sa = "none";
    class ia extends Pi {
      get $n() {
        return this.Cn;
      }
      set $n(e) {
        e !== this.Cn &&
          ((this.Cn = e),
          this.Sn &&
            ((this.Sn.dataset.display = `${e}`),
            this.Sn.dispatchEvent(
              new CustomEvent("dataDisplay", { detail: e })
            )));
      }
      constructor(e, t, s, i, o) {
        super(),
          (this.Vs = e),
          (this.fs = t),
          (this.In = s),
          (this.Ko = i),
          (this.Mr = o),
          (this.di = new ar("SearchBarWidgetComponent")),
          (this.Mn = !1),
          (this.Tn = !1),
          (this.An = !0),
          (this._n = []),
          (this.Cn = !1),
          (this.openPopup = () => !!this.En() && (this.On(), !0)),
          (this.closePopup = () => {
            if (((this.$n = !1), !this.Tn)) return;
            this.Tn = !1;
            const e = this.Pn();
            if (!e) return;
            const t = this.fs,
              s =
                "true" === e.getAttribute("aria-expanded")
                  ? this.footer.getSuggestionsList()
                  : this.Ln;
            s && t.addCSSClass(s, sa);
          }),
          (this.jn = (e) => {
            const t = e.target;
            t.isConnected &&
              !this.footer.element.contains(t) &&
              !this.Ln.contains(t) &&
              (this.closePopup(), this.Fn());
          }),
          (this.On = () => {
            this.Tn ||
              (this._n.forEach((e) => {
                this.fs.removeCSSClass(e, sa);
              }),
              this.Rn &&
                (this.Rn.setPinningVisibility(this._n.length > 0), this.Nn()),
              (this.Tn = !0),
              (this.$n = !0),
              this.fs.removeCSSClass(this.Ln, sa),
              this.Dn());
          }),
          (this.Hn = () => {
            var e;
            (null === (e = this.Rn) || void 0 === e ? void 0 : e.isPinned) ||
              this._n.forEach((e) => {
                this.fs.addCSSClass(e, sa);
              }),
              (this._n = []);
          });
        const {
          getSuggestions: r,
          sendMessage: a,
          uploadFile: n,
          onSpeechToggle: c,
          shareUserLocation: h,
          sendUserTypingStatusMessage: l,
          setHotkeyMap: p,
        } = this.In;
        this.Xi = this.Vs.name;
        (this.Un = new Ir(
          this.fs,
          (e) => {
            (this.$n = !1), a.call(s, e);
          },
          n.bind(s),
          this.Vs,
          r.bind(s),
          c.bind(s),
          h.bind(s),
          l.bind(s),
          this.Ko,
          s,
          p.bind(s)
        )),
          this.Vs.showTypingIndicator &&
            (this.Vn = new rr(to, this.Vs, this.fs));
      }
      get footer() {
        return this.Un;
      }
      get typingIndicator() {
        return this.Vn;
      }
      render() {
        const e = this.Vs,
          t = this.fs,
          s = document.getElementById(e.targetElement);
        let i;
        if (s) {
          this.Bn = t.createDiv(["search-bar-widget-wrapper", "wrapper"]);
          const e = t.createDiv(["search-bar-widget"]),
            o = t.createDiv(["search-bar-widget-content", sa]);
          (this.Ln = o),
            (i = t.createDiv(["search-bar-popup"])),
            (this.element = s),
            (this.In.element = s),
            this.footer.render();
          const r = this.footer.element,
            a = this.footer.getSuggestionsList();
          t.setChatWidgetWrapper(this.Bn);
          const n = t.createElement(
            "hr",
            ["search-bar-popup-separator", "none"],
            !1
          );
          (n.role = "none"), (this.Wn = n);
          const c = t.createDiv(["input-popup-slot"]);
          (c.id = `${this.Xi}-input-popup-slot`),
            c.addEventListener("closeSearchbarPopup", this.closePopup),
            (c.dataset.display = `${this.$n}`),
            (this.Sn = c),
            o.appendChild(i),
            o.append(n),
            o.appendChild(c),
            e.appendChild(o),
            r.append(e),
            this.Bn.appendChild(r);
          const h = t.createDiv(["input-end-slot"]);
          (h.id = `${this.Xi}-input-end-slot`),
            this.Bn.appendChild(h),
            s.appendChild(this.Bn),
            new Xr({
              parent: this.Ln,
              content: i,
              i18n: this.Mr,
              domUtil: this.fs,
            }),
            (this.qn = i),
            this.Dn(),
            Zn(r, "click", this.Dn),
            null == a ||
              a.addEventListener("click", () => {
                setTimeout(() => {
                  a.childElementCount && this.Fn();
                });
              }),
            this.In.loadPreviousConversations().then(() => {
              var e, t;
              const s = this._n.length > 0,
                o = (e) => {
                  var t;
                  this.Rn = new ta({
                    conversationContainer: i,
                    targetContainer: e,
                    isPinned:
                      (null === (t = this.Vs.pinningOptions) || void 0 === t
                        ? void 0
                        : t.isPinned) && s,
                    domUtil: this.fs,
                    closePopup: this.closePopup,
                    eventDispatcher: this.Ko,
                    footerTextArea: this.Pn(),
                    i18n: this.Mr,
                  });
                };
              if (
                null ===
                  (t =
                    null === (e = this.Vs) || void 0 === e
                      ? void 0
                      : e.pinningOptions) || void 0 === t
                  ? void 0
                  : t.pinElement
              )
                if (this.Vs.pinningOptions.pinElement instanceof HTMLElement)
                  o(this.Vs.pinningOptions.pinElement);
                else {
                  const e = 6e4;
                  ((e, t, s = 100) => {
                    const i = new C(),
                      o = performance.now() + t,
                      r = () => {
                        const t = document.getElementById(e);
                        t
                          ? i.resolve(t)
                          : performance.now() < o
                          ? setTimeout(r, s)
                          : i.reject();
                      };
                    return setTimeout(r, 0), i.promise;
                  })(this.Vs.pinningOptions.pinElement, e)
                    .then((e) => {
                      o(e);
                    })
                    .catch(() => {
                      this.di.error(
                        `Pin container ${this.Vs.pinningOptions.pinElement} not present after ${e}ms`
                      );
                    });
                }
              this.An = !0;
            });
        } else
          this.di.error(
            `Cannot fetch search bar using the passed target element: ${e.targetElement}`
          );
        return this.Zn(), this.Gn(), this.Yn(), this.Jn(), i;
      }
      appendMessageToConversation(e) {
        const t = this.qn;
        (t.textContent = ""),
          t.appendChild(e),
          this.fs.removeCSSClass(t.parentElement, sa),
          this.openPopup();
      }
      renderMessage(e, t, s) {
        const i = this.qn,
          o = this.fs,
          r = "skill-message";
        if (vt(e) && i) {
          const a = this.Kn(e, t, i);
          if (a) {
            cr(e)
              ? (o.addCSSClass(a, r),
                e.endOfTurn && ((this.An = !0), this._n.push(a)))
              : (o.addCSSClass(a, "user-message"),
                (this.An = !1),
                this.Hn(),
                this.Rn &&
                  (this.Rn.isVisible || this.Rn.setPinningVisibility(!0),
                  this.Rn.scrollToTop())),
              this.An || this._n.push(a);
            const t = this.Xn;
            s &&
            (null == t ? void 0 : t.className.includes(`${this.Vs.name}-${r}`))
              ? t.replaceWith(a)
              : (cr(e)
                  ? this.Qn
                    ? i.insertBefore(a, this.Qn.nextSibling)
                    : i.appendChild(a)
                  : i.prepend(a),
                (this.Qn = a)),
              (this.Xn = a);
          }
        }
      }
      showMessage(e, t) {
        const s = this.fs.getMessage(t.render());
        (s.id = e), this.qn.appendChild(s);
      }
      Kn(e, t, s) {
        const i = this.Vs.delegate;
        if (i && i.render) {
          const t = this.fs.createDiv(["message"]);
          (t.id = e.msgId), (t.lang = this.Vs.locale), s.appendChild(t);
          if (i.render(e)) return null;
          t.remove();
        }
        return t.render();
      }
      Dn() {
        this.Mn ||
          ((this.Mn = !0), document.addEventListener("click", this.jn, !0));
      }
      Fn() {
        this.Mn &&
          ((this.Mn = !1), document.removeEventListener("click", this.jn, !0));
      }
      En() {
        var e, t;
        const s = this.footer.getSuggestionsList();
        return (
          !(null == s ? void 0 : s.hasChildNodes()) &&
          !(!this.Ln && !this.Sn) &&
          (!!(null === (e = this.Sn) || void 0 === e
            ? void 0
            : e.hasChildNodes()) ||
            (0 !== this._n.length &&
              !(
                !0 ===
                (null === (t = this.Rn) || void 0 === t ? void 0 : t.isPinned)
              )))
        );
      }
      Nn() {
        var e, t, s;
        (null === (e = this.qn) || void 0 === e
          ? void 0
          : e.childElementCount) > 0 &&
        (null === (t = this.Sn) || void 0 === t
          ? void 0
          : t.childElementCount) > 0
          ? (null === (s = this.Rn) || void 0 === s ? void 0 : s.isPinned)
            ? this.ec()
            : this.tc()
          : this.ec();
      }
      tc() {
        this.fs.removeCSSClass(this.Wn, "none");
      }
      ec() {
        this.fs.addCSSClass(this.Wn, "none");
      }
      Zn() {
        const e = this.Pn(),
          t = () => {
            this.$n = !0;
          },
          s = () => {
            this.$n = !1;
          };
        Zn(e, "focus", () => {
          this.footer.isProgrammaticFocus() ? s() : t();
        }),
          Zn(e, "focus", this.openPopup),
          Zn(e, "blur", () => {
            this.Tn || s();
          }),
          Zn(e, "click", t),
          Zn(e, "click", this.openPopup),
          Zn(e, "keydown", () => {
            this.openPopup() || this.closePopup();
          }),
          Zn(e, "keyup", (e) => {
            var s;
            e.key !== F
              ? t()
              : (null === (s = this.Rn) || void 0 === s
                  ? void 0
                  : s.isPinned) && this.closePopup();
          });
      }
      Gn() {
        new MutationObserver((e) => {
          e.forEach((e) => {
            "childList" === e.type &&
              (e.addedNodes.length > 0
                ? this.$n && this.openPopup()
                : e.removedNodes.length > 0 && (this.En() || this.closePopup()),
              this.Nn());
          });
        }).observe(this.Sn, { childList: !0, subtree: !1 });
      }
      Yn() {
        new MutationObserver((e) => {
          e.forEach((e) => {
            "childList" === e.type &&
              (e.removedNodes.length > 0 && (this.En() || this.closePopup()),
              this.Nn());
          });
        }).observe(this.qn, { childList: !0, subtree: !1 });
      }
      Jn() {
        let e;
        Zn(this.Bn, "keydown", (t) => {
          t.key === U &&
            (e = setTimeout(() => {
              this.closePopup();
            }, 200));
        }),
          Zn(this.Bn, "keyup", (t) => {
            t.key === U && clearTimeout(e);
          });
      }
      Pn() {
        return this.footer.element.querySelector("textarea");
      }
    }
    var oa = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const ra = window.BroadcastChannel,
      aa = "collapsed",
      na = "expanded",
      ca = "large",
      ha = "none",
      la = setTimeout,
      pa = [Oe.Suggest, Oe.SessionClosed, Oe.CloseSession, Oe.Status],
      da = [Oe.Text, Oe.Attachment, Oe.Location, Oe.FormSubmission];
    class ua extends Pi {
      constructor(e, t, o) {
        var r, a, n;
        super(),
          (this.skillMessages = []),
          (this.contextWidgetMap = {}),
          (this.sc = []),
          (this.di = new ar("ChatComponent")),
          (this.oc = []),
          (this.rc = 0),
          (this.ac = []),
          (this.nc = !0),
          (this.cc = !0),
          (this.hc = !1),
          (this.lc = !1),
          (this.dc = !1),
          (this.uc = !0),
          (this.gc = !1),
          (this.mc = []),
          (this.bc = !1),
          (this.fc = 5e3),
          (this.wc = new Map()),
          (this.vc = !1),
          (this.xc = ""),
          (this.kc = !1),
          (this.yc = (e) =>
            oa(this, void 0, void 0, function* () {
              var t, o;
              if (Number.isInteger(e) && e !== i) {
                this.zc(),
                  this.Un.isDisabled() ||
                    (this.Un.disable(),
                    null === (t = this.Xa) || void 0 === t || t.disable(),
                    this.di.debug(
                      "WebSocket not open, send message button disabled"
                    )),
                  this.$c(),
                  e !== s || this.Vs.searchBarMode
                    ? this.hideTypingIndicator()
                    : this.showTypingIndicator();
                for (const e of this.oc)
                  this.Cc(e.fileName, ze.UploadNetworkFail, e.divId);
                this.Sc && this.Sc.disableComponent(!0);
              } else (this.Ic = void 0), this.hideTypingIndicator(), this.Un.isDisabled() && (this.Un.disable(!1), null === (o = this.Xa) || void 0 === o || o.disable(!1), this.di.debug("Connection established, send message button enabled")), this.Mc();
              this.Tc(e);
            })),
          (this.Ac = (e) =>
            oa(this, void 0, void 0, function* () {
              if (e) {
                const t = this.Vs;
                (t.URI = e.URI),
                  t.clientAuthEnabled ||
                    ((t.userId = e.userId), (t.channelId = e.channelId));
              }
              yield this._c(), this.Ec(), this.Oc();
            })),
          (this.Pc = (e) =>
            oa(this, void 0, void 0, function* () {
              const t = yield e.getPayload();
              this.fs.createAnchor(`tel:${t}`, "").click();
            })),
          (this.Lc = (e) =>
            oa(this, void 0, void 0, function* () {
              var t;
              const s = this.gi,
                i = yield e.getPayload();
              if (i instanceof HTMLElement) {
                const o = 2e3;
                try {
                  yield ((e) => {
                    const t = new ClipboardItem({
                      "text/html": new Blob([e.outerHTML], {
                        type: "text/html",
                      }),
                      "text/plain": new Blob([e.innerText], {
                        type: "text/plain",
                      }),
                    });
                    return navigator.clipboard.write([t]);
                  })(i),
                    this.jc(s.copySuccessMessage, Xa, o),
                    null === (t = e.onSuccess) || void 0 === t || t.call(e);
                } catch (e) {
                  this.jc(s.copyFailureMessage, sn, o);
                }
              } else this.Ko.trigger(i.actionType, i);
            })),
          (this.Fc = (e) => {
            this.shareUserLocation();
          }),
          (this.Rc = (e) => {
            this.Nc(e);
          }),
          (this.Dc = (e) =>
            oa(this, void 0, void 0, function* () {
              this.Hc(this.ac), this.Uc();
              const t = yield e.getPayload(),
                { label: s, imageUrl: i } = e,
                o = {};
              t["system.replaceMessage"] && (o.hidden = !0);
              const r = tt({
                postback: t,
                text: i ? this.fs.createImageIcon({ icon: i }).outerHTML : s,
                type: Oe.Postback,
              });
              try {
                this.sendMessage(r, o);
              } catch (e) {
                this.Vc(this.ac);
              }
            })),
          (this.Bc = (e) =>
            oa(this, void 0, void 0, function* () {
              if (navigator.share) {
                const t = yield e.getPayload();
                navigator.share({ text: t, title: e.label });
              } else this.jc(this.gi.shareFailureMessage, sn);
            })),
          (this.Wc = (e) =>
            oa(this, void 0, void 0, function* () {
              const t = e.messageComponent;
              if (!t.validateForm()) return;
              this.Uc();
              const s = t.getSubmittedFields();
              if (this.qc) {
                const e = this.getMessages();
                e
                  .slice()
                  .reverse()
                  .some((e) => {
                    if (
                      e.msgId !== t.msgId ||
                      e.messagePayload.type !== Oe.EditForm
                    )
                      return !1;
                    const i = e.messagePayload;
                    return (
                      Je(i)
                        ? i.fields.forEach((e) => {
                            It(e) || (e.defaultValue = s[e.id]);
                          })
                        : i.formRows.forEach((e) => {
                            e.columns.forEach((e) => {
                              e.fields.forEach((e) => {
                                It(e) || (e.defaultValue = s[e.id]);
                              });
                            });
                          }),
                      !0
                    );
                  }),
                  this.Zc.setItem(this.Gc, JSON.stringify(e));
              }
              const i = yield e.getPayload(),
                o = {
                  postback: i,
                  submittedFields: s,
                  type: Oe.FormSubmission,
                };
              i || delete o.postback;
              try {
                this.sendMessage(tt(o), { hidden: !0 });
              } catch (e) {
                this.Yc(e);
              }
            })),
          (this.Nc = (e) =>
            oa(this, void 0, void 0, function* () {
              const t = this.Vs,
                s = yield e.getPayload();
              this.fs
                .createAnchor(s, "", [], t.openLinksInNewWindow, t.linkHandler)
                .click();
            })),
          (this.Jc = (e) =>
            oa(this, void 0, void 0, function* () {
              const t = yield e.getPayload();
              this.fs
                .createAnchor(t, "", [], this.Vs.openLinksInNewWindow, this.Kc)
                .click();
            })),
          (this.Xc = {
            call: this.Pc,
            client: this.Lc,
            location: this.Fc,
            popup: this.Rc,
            postback: this.Dc,
            share: this.Bc,
            submitForm: this.Wc,
            url: this.Nc,
            webview: this.Jc,
          }),
          (this.Qc = (e) => {
            this.onSpeechToggle(!1);
            try {
              this.Xc[e.type](e);
            } catch (t) {
              this.di.warn("Error processing user action", e, t);
            }
          }),
          (this.eh = (e) => {
            e.showToUser &&
              "CAStatusError" === e.error &&
              this.jc(this.gi.connectionFailureMessage, Pa);
          }),
          (this.th = () => {
            var e;
            const t = this.Vs.searchBarMode ? this.sh.element : this.Un.element;
            P(t) &&
              (null === (e = this.sh) || void 0 === e || e.closePopup(),
              (this.vc = !0),
              this.Un.setRecognitionRequested(!0),
              this.Un.setVoiceRecording(!0),
              this.Uc(),
              (this.xc = (function (e, t) {
                const s = document.querySelector(`.${t}-wrapper`);
                return getComputedStyle(s).getPropertyValue(e);
              })("--color-visualizer", this.Vs.name)));
          }),
          (this.ih = () => {
            (this.vc = !1), this.Un.setVoiceRecording(!1);
          }),
          (this.oh = (e) => {
            const t = this.gi;
            let s = "";
            switch (null == e ? void 0 : e.message) {
              case fe.RecognitionMultipleConnection:
                s = t.errorSpeechMultipleConnection;
                break;
              case fe.RecognitionNotReady:
                s = t.errorSpeechInvalidUrl;
                break;
              case fe.RecognitionTooMuchSpeechTimeout:
              case fe.RecognitionProcessingFailure:
                s = t.errorSpeechTooMuchTimeout;
                break;
              case fe.RecognitionNoResponse:
                s = t.errorSpeechNoResponse;
                break;
              case fe.RecognitionNoWebServer:
                s = t.errorSpeechNoWebServer;
                break;
              default:
                s = t.errorSpeechUnavailable;
            }
            this.jc(s, sn), this.ih();
          }),
          (this.rh = (e) => {
            this.vc && this.ah(e);
          }),
          (this.nh = (e) => {
            this.vc && this.Un.updateVisualizer(e, this.xc);
          }),
          (this.Yc = (e) => {
            this.di.warn("[sendMessage] Failed to send message", e);
          }),
          (this.ph = () => {
            (this.dh = null),
              "action" !== this.Vs.focusOnNewMessage && this.Un.focusTextArea();
          }),
          (this.uh = () => {
            const e = this.dh;
            e && (this.gh.add(e), this.ca.cancelRequest(e)),
              this.mh(),
              this.bh(),
              this.fh(),
              this.hideTypingIndicator(),
              this.Un.disable(!1);
          }),
          (this.ca = e),
          (this.Vs = t),
          (this.Be =
            o && p(o.connect)
              ? o.connect
              : () => {
                  this.ca
                    .connect()
                    .catch((e) =>
                      this.di.error("Failed to connect to backend:", e)
                    );
                }),
          (this.wh = o && p(o.openChat) ? o.openChat : () => {}),
          (this.xh = o && p(o.closeChat) ? o.closeChat : () => {}),
          (this.Ko = (null == o ? void 0 : o.eventDispatcher) || G()),
          (this.kh =
            o && p(o.handleSessionEnd) ? o.handleSessionEnd : () => {}),
          (this.yh =
            o && p(o.receivedMessage)
              ? o.receivedMessage
              : (e) => {
                  this.Ko.trigger(ui.MESSAGE_RECEIVED, e),
                    this.Ko.trigger(ui.MESSAGE, e);
                }),
          (this.zh =
            o && p(o.sentMessage)
              ? o.sentMessage
              : (e) => {
                  this.Ko.trigger(ui.MESSAGE_SENT, e),
                    this.Ko.trigger(ui.MESSAGE, e);
                }),
          (this.Tc =
            o && p(o.onConnectionStatusChange)
              ? o.onConnectionStatusChange
              : () => {}),
          (this.$h =
            o && p(o.getUnreadMessagesCount)
              ? o.getUnreadMessagesCount
              : () => this.getUnreadMsgsCount()),
          (this.fs = (null == o ? void 0 : o.util) || new qn(this.Vs)),
          (this.Xi = this.Vs.name),
          (this.Ch = this.Vs.locale),
          (this.gi = Object.assign(
            Object.assign({}, this.Vs.i18n.en),
            this.Vs.i18n[this.Vs.locale]
          )),
          (this.isOpen = !1),
          (this.lc =
            "init" ===
              (null === (r = this.Vs.initMessageOptions) || void 0 === r
                ? void 0
                : r.sendAt) ||
            this.Vs.openChatOnLoad ||
            this.Vs.embedded),
          (this.hc = this.Vs.enableHeadless),
          (this.Sh =
            !this.Vs.embedded &&
            !this.Vs.sidepanel &&
            this.Vs.enableResizableWidget),
          (this.Ih = this.Vs.enableDefaultClientResponse),
          (this.qc =
            this.Vs.enableLocalConversationHistory &&
            this.Vs.storageType !== mr.CUSTOM),
          (this.Mh = { webCore: e, onMessageActionClicked: this.Qc }),
          (this.Th = "default"),
          this.Vs.enableTabsSync || (this.Ah = () => {}),
          this.Vs.threadId &&
            ((this.Vt = this.Vs.threadId),
            this.ca.setCurrentThreadId(this.Vs.threadId)),
          (this._h = (e) => {
            var t;
            if (!cr(e)) return;
            const {
              endOfTurn: s,
              messagePayload: i,
              requestId: o,
              threadId: r,
            } = e;
            if (this.gh.has(o)) return;
            s && (null === (t = this.Eh) || void 0 === t || t.hide());
            const a = Boolean(
              null == r ? void 0 : r.startsWith(`${Pe.UIWidget}:`)
            );
            let n;
            if ((a && (n = this.contextWidgetMap[r]), i)) {
              if (i.type === Oe.ExecuteApplicationActionCommand) {
                const e = i;
                return (
                  a ? n.showFullSizeWidget() : this.Oh(Boolean(s)),
                  void this.Ko.trigger(e.actionType, e)
                );
              }
              if (a) n.onMessageReceived(e);
              else {
                const t = i.type === Oe.Command && "noReply" === i.command;
                r !== this.Vt
                  ? this.Ph(r).then(() => {
                      t || this.Lh(e);
                    })
                  : t || this.Lh(e);
              }
            } else console.warn("Message Payload Not available");
          }),
          this.ca.on(_t.Open, this.Ac),
          this.ca.on(_t.State, this.yc),
          this.ca.on(_t.MessageReceived, this._h),
          this.ca.on(_t.CoreError, this.eh),
          this.ca.on(_t.ASRStart, this.th),
          this.ca.on(_t.ASRStop, this.ih),
          this.ca.on(_t.ASRError, this.oh),
          this.ca.on(_t.ASRResponse, this.rh),
          this.ca.on(_t.ASRVisualData, this.nh),
          this.Vs.enableVoiceOnlyMode &&
            ((this.jh = () => this.Fh()), this.ca.on(_t.TTSStop, this.jh)),
          this.Vs.enableBotAudioResponse &&
            (this.cc = this.Vs.initBotAudioMuted),
          this.Vs.searchBarMode
            ? ((this.sh = new ia(this.Vs, this.fs, this, this.Ko, this.gi)),
              (this.Un = this.sh.footer),
              (this.Vn = this.sh.typingIndicator),
              (this.Uc = () => {}),
              (this.updateNotificationBadge = () => {}),
              (this.Rh = () => {}))
            : ((this.Xa = new Lr(
                this.Vs,
                this.fs,
                null === (a = this.xh) || void 0 === a ? void 0 : a.bind(this),
                this.clearConversationHistory.bind(this),
                this.onToggleNarration.bind(this),
                this.ca,
                this.Nh.bind(this),
                this.setHotkeyMap.bind(this),
                this
              )),
              (this.Un = new Ir(
                this.fs,
                this.sendMessage.bind(this),
                this.uploadFile.bind(this),
                this.Vs,
                this.getSuggestions.bind(this),
                this.onSpeechToggle.bind(this),
                this.shareUserLocation.bind(this),
                this.sendUserTypingStatusMessage.bind(this),
                this.Ko,
                this,
                this.setHotkeyMap.bind(this)
              )),
              this.Vs.showTypingIndicator &&
                (this.Vn = new rr(to, this.Vs, this.fs)),
              "relative" === this.Vs.timestampMode ||
              "default" === this.Vs.timestampMode
                ? (this.Dh = new Qo(this.Vs, this.fs))
                : (this.Rh = () => {})),
          "action" !==
            (null === (n = this.Vs.focusOnNewMessage) || void 0 === n
              ? void 0
              : n.toLowerCase()) && (this.Hh = () => {}),
          this.configureStorage(),
          this.Uh(),
          this.ca.isConnected() && this.Oc();
      }
      render() {
        const e = this.Vs,
          t = this.fs;
        var s, o;
        "undefined" != typeof window &&
          (this.Vh(),
          (s = e.position),
          (o = t).updateCSSVar("--position-top", s.top || "unset"),
          o.updateCSSVar("--position-left", s.left || "unset"),
          o.updateCSSVar("--position-right", s.right || "unset"),
          o.updateCSSVar("--position-bottom", s.bottom || "unset"),
          s.bottom &&
            o.updateCSSVar(
              "--widget-max-height",
              `calc(100vh - 60px - ${s.bottom})`
            ),
          e.font && t.updateCSSVar("font", e.font),
          e.fontFamily && t.updateCSSVar("font-family", e.fontFamily),
          e.fontSize && t.updateCSSVar("font-size", e.fontSize)),
          e.searchBarMode
            ? (this.Bh = this.sh.render())
            : ((this.element = this._r()),
              this.Wh(),
              e.multiLangChat && this.qh());
        const r = this.ca.getState();
        this.yc(r),
          r === i && this.Ac(),
          this.Zh(e),
          e.searchBarMode || this.loadPreviousConversations();
      }
      embedInElement(e) {
        const t = document.getElementById(e);
        if (!t) throw new Error("Can not embed chat widget.");
        this.fs.addCSSClass(t, "wrapper", this.Vs.theme, "embedded"),
          this.appendToElement(t);
      }
      showChat() {
        if (!this.isOpen) {
          const e = this.fs;
          e.removeCSSClass(this.element, aa),
            e.addCSSClass(this.element, na),
            e.removeCSSClass(this.chatWidgetDiv, ha),
            this.Vs.embedded ||
              la(() => {
                e.addCSSClass(this.Gh, ha);
              }, 250),
            (this.isOpen = !0),
            (this.lc = !0),
            this.updateNotificationBadge(0),
            this.Uc(),
            this.Un.focusTextArea(),
            this.Oc(),
            this.kc && (this.Fh(), (this.kc = !1));
        }
      }
      onClose() {
        if (this.isOpen) {
          const e = this.fs;
          this.mh();
          this.Un.getInputMode() === $r && ((this.kc = !0), this.Yh()),
            e.removeCSSClass(this.element, na),
            e.addCSSClass(this.element, aa),
            this.Vs.embedded ||
              (e.removeCSSClass(this.Gh, ha),
              la(() => {
                e.addCSSClass(this.chatWidgetDiv, ha), this.Gh.focus();
              }, 250),
              this.updateNotificationBadge(this.$h())),
            (this.isOpen = !1);
        }
      }
      sendExitEvent() {
        const e = {
          messagePayload: { type: Oe.CloseSession },
          userId: this.Vs.userId,
        };
        if (
          this.Vs.delegate &&
          this.Vs.delegate.beforeEndConversation &&
          p(this.Vs.delegate.beforeEndConversation)
        )
          try {
            this.Vs.delegate.beforeEndConversation(e).then((e) => {
              e &&
                this.sendMessage(e, { hidden: !0, delegate: !1 }).catch(
                  this.Yc
                );
            });
          } catch (e) {
            this.di.error(e);
          }
        else this.sendMessage(e, { hidden: !0, delegate: !1 }).catch(this.Yc);
        this.hc = !1;
      }
      updateNotificationBadge(e) {
        var t;
        (this.rc = e),
          e > 0
            ? this.Jh &&
              ((this.Jh.innerText = `${e}`), this.Gh.appendChild(this.Jh))
            : (null === (t = this.Jh) || void 0 === t
                ? void 0
                : t.parentElement) && this.Jh.remove();
      }
      onToggleNarration(e) {
        this.Kh(e), this.Ko.trigger(ui.CLICK_AUDIO_RESPONSE_TOGGLE, e);
      }
      remove() {
        var e;
        super.remove(),
          null === (e = this.Xa) || void 0 === e || e.remove(),
          this.ca.off(_t.Open, this.Ac),
          this.ca.off(_t.State, this.yc),
          this.ca.off(_t.MessageReceived, this._h),
          this.ca.off(_t.CoreError, this.eh),
          this.ca.off(_t.ASRStart, this.th),
          this.ca.off(_t.ASRStop, this.ih),
          this.ca.off(_t.ASRError, this.oh),
          this.ca.off(_t.ASRResponse, this.rh),
          this.ca.off(_t.ASRVisualData, this.nh),
          this.jh && this.ca.off(_t.TTSStop, this.jh),
          this.Vs.embedded && window.removeEventListener("resize", this.Xh);
        const t = this.Qh;
        t && t.remove(),
          this.Vs.enableSpeech &&
            window.removeEventListener("visibilitychange", this.el);
      }
      clearConversationHistory(e = !1) {
        e
          ? this.tl(e)
          : (this.clearMessages(this.Vs.userId),
            this.tl(),
            this.sl({ type: "actionClearHistory" })),
          (this.il = null),
          (this.mc = []),
          (this.skillMessages = []),
          this.Oh(),
          this.updateNotificationBadge(0);
      }
      clearMessages(e, t) {
        const s = this.Vs;
        if (s.storageType === mr.CUSTOM) {
          const e = s.conversationHistoryProvider;
          p(null == e ? void 0 : e.deleteMessages)
            ? e.deleteMessages({ threadId: s.threadId })
            : this.di.warn(
                "Can not clear conversation history. Pass conversationHistoryProvider object with deleteMessages function when custom storage is enabled."
              );
        } else {
          const i = `${s.name}-${e}-messages`;
          (t ? window[t] : this.Zc).getItem(i) && this.Zc.removeItem(i);
        }
      }
      clearAllMessage() {
        const e =
            null === window || void 0 === window ? void 0 : window.localStorage,
          t = (null == e ? void 0 : e.length) || 0;
        if (t) {
          const s = /oda-chat-.*-messages/g;
          for (let i = 0; i < t; i++) {
            const t = e.key(i);
            (null == t ? void 0 : t.match(s)) && e.removeItem(t);
          }
        }
      }
      setUserInputMessage(e) {
        this.Un.setUserInputText(e);
      }
      setUserInputPlaceholder(e) {
        this.Un.setUserInputPlaceholder(e);
      }
      getWebViewComponent() {
        return this.ol;
      }
      refreshWebView(e) {
        this.ol.setProps(e),
          this.rl.remove(),
          (this.rl = this.ol.render()),
          this.chatWidgetDiv.appendChild(this.rl);
      }
      orientWidgetAnimation() {
        const e = this.element,
          t = Math.floor(window.innerWidth / 2),
          s = e.offsetLeft;
        s < 0
          ? (e.style.left = "10px")
          : s > window.innerWidth && (e.style.right = "10px"),
          s < t && this.fs.addCSSClass(e, "pos-left");
      }
      updateFullScreenWidth(e) {
        const t = this.Vs.sidepanel
            ? this.chatWidgetWrapper
            : this.chatWidgetDiv,
          s = this.fs;
        if ((s.updateCSSVar("--width-full-screen", e), t)) {
          const i = "default",
            o = "medium",
            r = "size",
            a = parseInt(e);
          if (a >= 1024) {
            if (this.Th === ca) return;
            const e = this.Vs.icons;
            s.addCSSClass(t, `${ca}-${r}`),
              s.addCSSClass(
                this.Un.element,
                e.avatarBot || e.avatarAgent ? "left" : "",
                e.avatarUser ? "right" : ""
              ),
              s.removeCSSClass(t, `${o}-${r}`),
              (this.Th = ca);
          } else if (a >= 600) {
            if (this.Th === o) return;
            s.addCSSClass(t, `${o}-${r}`),
              s.removeCSSClass(t, `${ca}-${r}`),
              (this.Th = o);
          } else {
            if (this.Th === i) return;
            s.removeCSSClass(t, `${o}-${r}`),
              s.removeCSSClass(t, `${ca}-${r}`),
              (this.Th = i);
          }
          this.Un.updateInputHeight(),
            this.skillMessages
              .filter((e) => e instanceof Fo)
              .forEach((e) => {
                e.setCardsScrollAttributes(this.Th);
              }),
            this.Uc();
        }
      }
      setHeight(e) {
        const t = this.chatWidgetDiv;
        t && !this.Vs.sidepanel && ((t.style.height = e), (this.Vs.height = e));
      }
      setWidth(e) {
        const t = this.Vs.sidepanel
          ? this.chatWidgetWrapper
          : this.chatWidgetDiv;
        t &&
          ((t.style.width = e),
          (this.Vs.width = e),
          this.updateFullScreenWidth(e));
      }
      setSize(e, t) {
        this.setHeight(t), this.setWidth(e);
      }
      setMessagePadding(e) {
        this.al("message-bubble", { padding: e }), (this.Vs.messagePadding = e);
      }
      setChatBubbleIconHeight(e) {
        this.al("typing-cue-wrapper", { height: e }), (this.Vs.height = e);
      }
      setChatBubbleIconWidth(e) {
        this.al("typing-cue-wrapper", { width: e }), (this.Vs.width = e);
      }
      setChatBubbleIconSize(e, t) {
        this.al("typing-cue-wrapper", { height: t, width: e }),
          (this.Vs.width = e),
          (this.Vs.height = t);
      }
      applyDelegates(e) {
        var t;
        let s;
        s =
          "string" == typeof e
            ? Qe(
                e,
                null === (t = this.speechFinalResult) || void 0 === t
                  ? void 0
                  : t.speechId
              )
            : Ze(e)
            ? et(e)
            : qe(e)
            ? tt(e)
            : e;
        const i = s.messagePayload.type,
          o = this.Vs.delegate,
          r = o.beforePostbackSend,
          a = o.beforeSend;
        return (
          i === Oe.Postback && p(r)
            ? (s = this.cl(s, r))
            : da.includes(i) && p(a) && (s = this.cl(s, a)),
          s
        );
      }
      sendMessage(e, t) {
        if (this.hl) return ga();
        this.Oh(),
          !this.Vs.enableSpeechAutoSend &&
            this.speechFinalResult &&
            "string" == typeof e &&
            e
              .toLowerCase()
              .includes(this.speechFinalResult.text.toLowerCase()) &&
            (e = Qe(e, this.speechFinalResult.speechId)),
          this.Un.focusTextArea(),
          this.mh(),
          void 0 === (t = t || {}).delegate && (t.delegate = !0),
          t.delegate && this.Vs.delegate && (e = this.applyDelegates(e));
        const s = this.Vs.sdkMetadata
          ? Object.assign({ version: mi }, this.Vs.sdkMetadata)
          : { version: mi };
        return (
          e &&
          this.ca.sendMessage(e, { sdkMetadata: s }).then((s) => {
            var i, o;
            (this.di.debug("onMessageSent", e),
            (o = s.messagePayload),
            !qe(o) ||
              (o.type !== Oe.InboundEvent && o.type !== Oe.OutboundEvent)) &&
              ((this.dh = s.requestId),
              null === (i = this.zh) || void 0 === i || i.call(this, s),
              this.ll(),
              (this.gc = !1),
              this.Ih && this.pl(),
              (this.speechFinalResult = null),
              (null == t ? void 0 : t.hidden) ? (this.il = Ue) : this.dl(s),
              this.getAgentDetails() || this.showTypingIndicator());
          })
        );
      }
      uploadFile(e, t) {
        if (this.hl) return ga();
        const s = this.gi;
        this.mh(), this.ll();
        const i = new Promise((i, o) => {
          var r;
          if (this.Vs.enableHeadless) {
            const t = this.Vs.sdkMetadata
              ? Object.assign({ version: mi }, this.Vs.sdkMetadata)
              : { version: mi };
            this.ca
              .uploadAttachment(e, { sdkMetadata: t })
              .then((e) =>
                this.ca.sendMessage(
                  this.Vs.delegate ? this.applyDelegates(e) : e,
                  { sdkMetadata: t }
                )
              )
              .then(i)
              .catch(o);
          } else {
            this.Uc();
            const a =
                null === (r = e.name) || void 0 === r
                  ? void 0
                  : r.replace(/[\s:'"\\/[\]~,.;^`()@#%*+=$&!{}?<>|]/g, ""),
              n = ae({ prefix: a }),
              c = this.fs.createDiv();
            if (
              ((c.id = n),
              this.oc.push({ divId: n, fileName: e.name }),
              this.ul(new Date()),
              this.gl(c),
              (this.ml = this.customFileMaxSize
                ? this.customFileMaxSize
                : t
                ? t.maxSize
                : fi),
              e.size > this.ml)
            ) {
              this.Uc();
              const t = this.ml / 1048576;
              let i = t.toString();
              xn(t) || (i = t.toFixed(3));
              const r = `${e.name} - ${s.uploadFailed}`,
                a = s.uploadFileSizeLimitExceeded.replace("{0}", i);
              this.bl(r, a, n), this.Rh(Ue), o(new Error(a));
            } else if (0 === e.size) {
              this.Uc();
              const t = `${e.name} - ${s.uploadFailed}`,
                i = s.uploadFileSizeZeroByte;
              this.bl(t, i, n), this.Rh(Ue), o(new Error(i));
            } else {
              const t = new Vo(e.name, so, this.Vs, this.fs),
                s = this.Vs.sdkMetadata
                  ? Object.assign({ version: mi }, this.Vs.sdkMetadata)
                  : { version: mi };
              this.Rh(Ue),
                c.appendChild(t.render()),
                this.Uc(),
                this.ca
                  .uploadAttachment(e, { sdkMetadata: s })
                  .then((e) =>
                    this.ca.sendMessage(
                      this.Vs.delegate ? this.applyDelegates(e) : e,
                      { sdkMetadata: s }
                    )
                  )
                  .then((t) => {
                    var s;
                    (t.messagePayload.attachment.title = e.name),
                      c.remove(),
                      (this.oc = this.oc.filter((e) => e.divId !== n)),
                      (this.uc = !1),
                      null === (s = this.zh) || void 0 === s || s.call(this, t),
                      this.dl(t),
                      i(t);
                  })
                  .catch((t) => {
                    this.Cc(e.name, t.message, n), o(t);
                  });
            }
          }
        });
        return (
          i.catch((e) => {
            this.di.error(e);
          }),
          i
        );
      }
      refreshTTS() {
        this.Xa.showTTSButton(!!this.Vs.ttsService);
      }
      getSuggestions(e) {
        if (this.hl) return ga();
        if (
          !this.Vs.enableAutocompleteClientCache ||
          (this.Vs.enableAutocompleteClientCache &&
            !this.Un.getSuggestionsValid())
        )
          return this.ca
            .getSuggestions(e)
            .then((e) => (this.Un.displaySuggestions(e), e))
            .catch(
              (e) => (
                this.di.debug(
                  "[getSuggestions] Failed to receive suggestions, reset list:",
                  e
                ),
                []
              )
            );
        const t = this.fl(this.Un.getSuggestions(), e);
        return (
          null !== this.Un && this.Un.displaySuggestions(t), Promise.resolve(t)
        );
      }
      getUnreadMsgsCount() {
        return this.rc;
      }
      getMessages() {
        const e = this.Zc.getItem(this.Gc);
        let t = [];
        if (e)
          try {
            t = JSON.parse(e).map((e) => Object.assign({}, e));
          } catch (e) {
            this.di.error("Failed to parse saved chat.");
          }
        return t;
      }
      getAgentDetails() {
        return this.wl;
      }
      setAgentDetails(e) {
        (this.wl = Object.assign(Object.assign({}, this.wl), e)),
          this.vl(),
          this.Zc.setItem(this.xl, JSON.stringify(this.wl));
      }
      setUserAvatar(e) {
        (this.Vs.icons.avatarUser = e), this.Zc.setItem(this.kl, e);
        document
          .querySelectorAll(`.${this.Xi}-right .${this.Xi}-message-icon`)
          .forEach((t) => {
            t.parentElement.replaceWith(this.yl(e, this.gi.avatarUser));
          });
      }
      zl(e) {
        if (!vt(e)) return;
        const t = Object.assign({ date: Date.now() }, e);
        if ((this.sc.push(t), this.Vs.storageType === mr.CUSTOM)) {
          const e = this.Vs.conversationHistoryProvider;
          p(null == e ? void 0 : e.saveMessage)
            ? e.saveMessage(t)
            : this.di.warn(
                "Can not save conversation history. Pass conversationHistoryProvider object with saveMessage function when custom storage is enabled."
              );
        } else if (this.qc) {
          const e = this.getMessages();
          e.length >= this.Vs.messageCacheSizeLimit &&
            e.splice(0, e.length - (this.Vs.messageCacheSizeLimit - 1)),
            e.push(t),
            this.Zc.setItem(this.Gc, JSON.stringify(e));
        }
      }
      configureStorage() {
        const e = this.Vs,
          { storageType: t, userId: s } = e;
        this.qc &&
          (s
            ? t !== mr.LOCAL && t !== mr.SESSION && (e.storageType = mr.LOCAL)
            : (e.storageType = mr.SESSION)),
          (this.Zc = new kr(e.storageType));
      }
      setVoiceRecognitionService(e) {
        this.Un.disableVoiceModeButton(!e, { src: "lang" });
      }
      enableSpeechSynthesisService(e) {
        this.Xa.disableTTSButton(!e);
      }
      onShareLocation() {
        this.shareUserLocation();
      }
      setPrimaryChatLanguage(e) {
        this.Sc.setTag(e);
      }
      onLanguageUpdate(e, t = !0) {
        var s;
        const i = this.Vs.i18n,
          o = Object.assign(
            Object.assign(Object.assign({}, i.en), i[this.Vs.locale]),
            i[e]
          );
        t && this.sl({ type: "actionLanguage", tag: e }),
          (this.Ch = e),
          (this.Gh.title = o.chatButtonTitle || o.chatTitle),
          this.Xa.setLocale(o),
          this.Un.setLocale(o),
          this.Vs.showTypingIndicator &&
            this.Vn.updateTypingCueLocale(o.typingIndicator);
        document.querySelectorAll(`.${this.Xi}-message-icon`).forEach((e) => {
          const t = e.parentElement.parentElement.className.includes(
            `${this.Xi}-left`
          )
            ? o.avatarBot
            : o.avatarUser;
          "img" === e.localName ? (e.alt = t) : e.setAttribute("aria-label", t);
        }),
          this.refreshWebView({
            accessibilityTitle: o.webViewAccessibilityTitle,
            closeButtonLabel: o.webViewClose,
            errorInfoDismissLabel: o.webViewErrorInfoDismiss,
            errorInfoText: o.webViewErrorInfoText,
          }),
          this.Sc && this.Sc.setLocale(o),
          this.$l &&
            (this.$l.textContent = Y(this.Cl, {
              pattern: this.Vs.timestampFormat,
              locale: e,
            })),
          this.Dh && this.Dh.setLocale(o),
          this.Sl && (this.Sl.innerText = o.previousChats),
          null === (s = this.Eh) || void 0 === s || s.setLocale(o),
          (this.gi = o);
      }
      showTypingIndicator() {
        const e = document.getElementById(`${this.Xi}-connection-error`);
        e && e.remove(),
          this.Vs.showTypingIndicator &&
            (this.Vs.searchBarMode
              ? this.Vn.append(this.Bh)
              : (this.Vn.append(this.wn), this.Uc()));
      }
      hideTypingIndicator() {
        this.Vs.showTypingIndicator && this.Vn.remove();
      }
      showConnectionError() {
        const e = {
            messagePayload: {
              type: Oe.Text,
              text: _(this.gi.connectionFailureMessage),
              globalActions: [
                { type: $e.Postback, label: this.gi.connectionRetryLabel },
              ],
            },
            source: Be,
          },
          t = pr.fromMessage(
            this.Vs,
            this.fs,
            e,
            Object.assign(Object.assign({}, this.Mh), {
              onMessageActionClicked: () => {
                this.Be();
              },
              locale: this.Ch,
            })
          );
        this.showMessage(`${this.Xi}-connection-error`, t);
      }
      showMessage(e, t) {
        var s;
        if (this.Vs.searchBarMode) this.sh.showMessage(e, t);
        else {
          const s = this.fs.wrapMessageBlock(
            t.render(),
            this.Vs.icons.avatarBot,
            to
          );
          (s.id = e), this.wn.appendChild(s);
        }
        (null === (s = this.Vn) || void 0 === s ? void 0 : s.isVisible()) &&
          this.hideTypingIndicator(),
          this.Uc();
      }
      showWidget() {
        this.Il(!0);
      }
      hideWidget() {
        this.Il(!1);
      }
      Il(e) {
        const t = this.Vs;
        if (t.embedded || t.enableHeadless) return;
        const s = this.chatWidgetWrapper,
          i = `${this.fs.cssPrefix}-none`;
        s &&
          s.classList.contains(i) === e &&
          (s.classList.toggle(i),
          this.Ko.trigger(e ? ui.WIDGET_SHOW : ui.WIDGET_HIDE));
      }
      Ml(e) {
        if (((this.uc = !1), !this.gc)) {
          const t = {
            source: Be,
            messagePayload: { type: Oe.Text, text: e },
            userId: this.Vs.userId,
            msgId: `${Date.now()}`,
          };
          this.zl(t), this.Tl(e), this.Al([t]);
        }
      }
      pl() {
        const e = this.gi;
        this._l = la(() => {
          this.uc && this.Ml(e.defaultGreetingMessage),
            (this.El = setInterval(() => {
              this.Ml(e.defaultWaitMessage);
            }, this.Vs.defaultWaitMessageInterval * wi)),
            (this.Ol = la(() => {
              clearInterval(this.El);
            }, (this.Vs.typingIndicatorTimeout - 1) * wi)),
            (this._l = la(() => {
              this.hideTypingIndicator(), this.Ml(e.defaultSorryMessage);
            }, this.Vs.typingIndicatorTimeout * wi));
        }, this.Vs.defaultGreetingTimeout * wi);
      }
      _c() {
        return oa(this, void 0, void 0, function* () {
          if (this.Vs.clientAuthEnabled)
            try {
              const e = yield this.ca.getAuthToken();
              (this.Vs.channelId = e.getClaim("channelId")),
                (this.Vs.userId = e.getClaim("userId"));
            } catch (e) {
              return;
            }
          const { name: e, userId: t } = this.Vs,
            s = `${e}-${t}`;
          (this.Gc = `${s}-messages`),
            (this.xl = `${s}-agent-details`),
            (this.kl = `${s}-user-avatar`);
        });
      }
      Ec() {
        (this.Pl = `${this.Vs.userId}-canceled-requests`),
          (this.gh = new Set(this.Ll())),
          this.Ah();
      }
      qh() {
        const e = this.Vs;
        (this.Sc = new Rr(
          e.multiLangChat,
          {
            webCore: this.ca,
            chatWidget: this,
            eventDispatcher: this.Ko,
            settings: e,
            synthesisVoices: e.ttsVoice,
            storageService: new kr(e.storageType),
            util: this.fs,
          },
          this
        )),
          this.Xa.addLanguageSelect(this.Sc);
      }
      shareUserLocation() {
        const e = this.gi;
        if (navigator && navigator.geolocation) {
          const t = new Vo(e.requestLocation, so, this.Vs, this.fs);
          this.gl(t.render()),
            this.Uc(),
            Rt().then(
              (e) => {
                const s = tt({
                  location: {
                    latitude: e.latitude,
                    longitude: e.longitude,
                    title: void 0,
                  },
                  type: Oe.Location,
                });
                t.remove(), this.sendMessage(s).catch(this.Yc);
              },
              (s) => {
                let i;
                switch (s.code) {
                  case s.PERMISSION_DENIED:
                    i = e.requestLocationDeniedPermission;
                    break;
                  case s.POSITION_UNAVAILABLE:
                    i = e.requestLocationDeniedUnavailable;
                    break;
                  case s.TIMEOUT:
                    i = e.requestLocationDeniedTimeout;
                    break;
                  default:
                    i = e.requestLocationDeniedPermission;
                }
                this.jc(i, sn), t.remove();
              }
            );
        } else this.jc(e.requestLocationDeniedUnavailable, sn);
      }
      fl(e, t) {
        const s = [];
        for (const i of e) i.search(new RegExp(t, "i")) >= 0 && s.push(i);
        return s;
      }
      Cc(e, t, s) {
        const i = this.gi,
          o = `${e} - ${i.uploadFailed}`;
        let r = "";
        switch (t) {
          case ze.UploadMaxSize:
            r = i.uploadFileSizeLimitExceeded.replace(
              "{0}",
              this.ml.toString()
            );
            break;
          case ze.UploadZeroSize:
            r = i.uploadFileSizeZeroByte;
            break;
          case ze.UploadBadFile:
            r = i.uploadUnsupportedFileType;
            break;
          case ze.UploadNetworkFail:
            r = i.uploadFileNetworkFailure;
            break;
          case ze.UploadUnauthorized:
            r = i.uploadUnauthorized;
        }
        this.bl(o, r, s);
      }
      cl(e, t) {
        var s;
        const i = d(e);
        let o,
          r = d(e);
        e.messagePayload.type === Oe.Text &&
          (null === (s = e.sdkMetadata) || void 0 === s
            ? void 0
            : s.speechId) &&
          (o = (e.messagePayload.text || "").toLowerCase());
        try {
          r = t(i);
        } catch (e) {
          this.di.error(e);
        }
        if (
          ((null == r ? void 0 : r.messagePayload) || (r = null),
          r &&
            !xt(r) &&
            (this.di.error(
              "The generated delegate message is invalid. Sending original message instead."
            ),
            (r = e)),
          o && r)
        )
          if (r.messagePayload)
            if (r.messagePayload.type === Oe.Text) {
              const e = r.messagePayload.text;
              (null == e ? void 0 : e.toLowerCase().indexOf(o)) < 0 &&
                delete r.sdkMetadata;
            } else delete r.sdkMetadata;
          else delete r.sdkMetadata;
        return r;
      }
      bl(e, t, s) {
        const i = document.getElementById(s);
        if (i) {
          i.firstElementChild && i.removeChild(i.firstElementChild),
            (this.oc = this.oc.filter((e) => e.divId !== s));
          const o = new Wo(e, t, so, this.Vs, this.fs, !0),
            r = this.Vs.icons.error || Pa;
          i.appendChild(o.render(r));
        }
      }
      addHeaderAction(e) {
        this.Xa.addAction(e);
      }
      updateHeaderAction(e) {
        this.Xa.updateHeaderAction(e);
      }
      on(e, t) {
        switch (e) {
          case ye.TTSStart:
          case ye.TTSStop:
            this.ca.on(e, t);
            break;
          default:
            this.Ko.bind(e, t);
        }
      }
      off(e, t) {
        switch (e) {
          case ye.TTSStart:
          case ye.TTSStop:
            this.ca.off(e, t);
            break;
          default:
            this.Ko.unbind(e, t);
        }
      }
      _r() {
        var e, t, s, i, o, r;
        const a = this.Vs,
          n = this.fs,
          c = this.gi,
          h = n.createDiv(
            a.embedded
              ? []
              : ["wrapper", a.theme, a.enableHeadless ? "none" : ""]
          );
        (this.chatWidgetDiv = n.createDiv(["widget", "flex", "col"])),
          this.chatWidgetDiv.setAttribute("role", "region"),
          this.chatWidgetDiv.setAttribute(
            "aria-labelledby",
            `${this.Xi}-title`
          ),
          this.fs.setChatWidgetWrapper(h);
        const l = this.Xa.render();
        this.chatWidgetDiv.appendChild(this.Xa.element),
          a.embedTopStickyId &&
            this.jl(a.embedTopStickyId, this.chatWidgetDiv, [
              "embed-sticky-top",
            ]),
          (this.Fl = new Fr(n)),
          !a.enableCancelResponse ||
            a.enableHeadless ||
            a.searchBarMode ||
            (this.Eh = new Hr({
              parent: this.Fl.element,
              i18n: this.gi,
              domUtil: this.fs,
              onHide: this.ph,
              onClick: this.uh,
            })),
          (this.Rl = n.createDiv([
            "conversation-pane",
            a.icons.avatarBot ? "bot-icon" : "",
            a.icons.avatarUser ? "user-icon" : "",
          ])),
          "bottom" === a.conversationBeginPosition &&
            (this.Rl.style.marginTop = "auto"),
          a.embedTopScrollId &&
            this.jl(a.embedTopScrollId, this.Rl, ["embed-scroll-top"]),
          (this.wn = n.createDiv(["conversation-container"])),
          this.wn.setAttribute("role", "log"),
          this.wn.setAttribute("aria-live", "polite"),
          this.wn.setAttribute("aria-atomic", "false"),
          this.Rl.appendChild(this.wn),
          this.Fl.element.appendChild(this.Rl),
          a.embedBottomScrollId &&
            this.jl(a.embedBottomScrollId, this.Fl.element, [
              "embed-scroll-bottom",
            ]),
          this.chatWidgetDiv.appendChild(this.Fl.element),
          a.embedBottomStickyId &&
            this.jl(a.embedBottomStickyId, this.chatWidgetDiv, [
              "embed-sticky-bottom",
            ]),
          this.Un.render(),
          this.chatWidgetDiv.appendChild(this.Un.element),
          (t = a.webViewConfig).accessibilityTitle ||
            (t.accessibilityTitle = c.webViewAccessibilityTitle),
          (s = a.webViewConfig).closeButtonLabel ||
            (s.closeButtonLabel = c.webViewClose),
          (i = a.webViewConfig).errorInfoDismissLabel ||
            (i.errorInfoDismissLabel = c.webViewErrorInfoDismiss),
          (o = a.webViewConfig).errorInfoText ||
            (o.errorInfoText = c.webViewErrorInfoText),
          (r = a.webViewConfig).closeButtonIcon ||
            (r.closeButtonIcon = a.icons.close),
          (this.ol = new Jr(a.webViewConfig, n, a)),
          (this.rl = this.ol.render()),
          this.chatWidgetDiv.appendChild(this.rl);
        const p = this.ol,
          d = `${this.Xi}-webview`;
        if (
          ((this.Kc = {
            target: d,
            onclick: function () {
              p.open(this.href);
            },
          }),
          a.linkHandler &&
            a.linkHandler.target === d &&
            (a.linkHandler = this.Kc),
          (this.Mh = {
            webviewLinkHandler: this.Kc,
            webCore: this.ca,
            onMessageActionClicked: this.Qc,
          }),
          h.appendChild(this.chatWidgetDiv),
          a.embedded)
        )
          (this.isOpen = !0), n.addCSSClass(h, "open");
        else {
          const t =
              a.icons.launch ||
              (a.colors && a.colors.branding
                ? Ua.replace("#025e7e", a.colors.branding)
                : Ua),
            s = "button",
            i = n.createIconButton({
              css: [s],
              icon: t,
              iconCss: [`${s}-icon`],
              title: c.chatButtonTitle || c.chatTitle,
            });
          i.classList.remove(`${this.Xi}-icon`),
            (this.Gh = i),
            (this.Gh.onclick =
              null === (e = this.wh) || void 0 === e ? void 0 : e.bind(this)),
            (this.Jh = n.createTextDiv(["notification-badge"])),
            h.appendChild(i),
            this.wc.set("launch", i),
            a.enableDraggableButton &&
              new Jn(this.fs, i).makeElementDraggable(),
            a.enableDraggableWidget &&
              new Jn(this.fs, l, this.chatWidgetDiv).makeElementDraggable(),
            a.openChatOnLoad || n.addCSSClass(h, aa),
            n.addCSSClass(this.chatWidgetDiv, ha);
        }
        if (((this.chatWidgetWrapper = h), a.sidepanel)) {
          const e = (e) => {
            const t = document.body.clientWidth - e.x;
            if (
              (n.addCSSClass(this.chatWidgetWrapper, "drag"),
              (document.body.style.cursor =
                t <= 375 ? "w-resize" : t >= 800 ? "e-resize" : "col-resize"),
              t >= 375 && t <= 800)
            ) {
              const e = `${t}px`;
              (this.chatWidgetWrapper.style.width = e),
                this.updateFullScreenWidth(e);
            }
            e.preventDefault();
          };
          h.addEventListener(
            "mousedown",
            (t) => {
              t.offsetX < 4 && document.addEventListener("mousemove", e, !1);
            },
            !1
          ),
            document.addEventListener(
              "mouseup",
              () => {
                document.removeEventListener("mousemove", e, !1),
                  n.removeCSSClass(this.chatWidgetWrapper, "drag"),
                  this.chatWidgetWrapper.style.removeProperty("cursor"),
                  document.body.style.removeProperty("cursor");
              },
              !1
            );
        } else if (this.Sh) {
          new zc(
            this.chatWidgetDiv,
            this.updateFullScreenWidth.bind(this),
            n
          ).makeWidgetResizable();
        }
        if (this.Vs.enableSpeech) {
          let e = this.Un.getInputMode(),
            t = !1;
          (this.el = () => {
            (e = this.Un.getInputMode()),
              this.isOpen &&
                (document.hidden && e === $r
                  ? ((t = !0), this.Yh())
                  : !document.hidden && t && (this.Fh(), (t = !1)));
          }),
            window.addEventListener("visibilitychange", this.el);
        }
        return this.chatWidgetWrapper;
      }
      Vh() {
        const e = this.Vs;
        if (!e.disableInlineCSS) {
          let e = !1;
          const t = document.head.children,
            s = document.createElement("style");
          s.appendChild(
            document.createTextNode(
              '@keyframes scale-in-center{0%{opacity:1;transform:scale(0)}100%{opacity:1;transform:scale(1)}}@keyframes scale-out-center{0%{display:flex;opacity:1;transform:scale(1)}100%{display:none;opacity:1;transform:scale(0)}}@keyframes scale-in-br{0%{opacity:1;transform:scale(0);transform-origin:100% 100%}100%{opacity:1;transform:scale(1);transform-origin:100% 100%}}@keyframes scale-in-bl{0%{opacity:1;transform:scale(0);transform-origin:0 100%}100%{opacity:1;transform:scale(1);transform-origin:0 100%}}@keyframes scale-in-tl{0%{opacity:1;transform:scale(0);transform-origin:0 0}100%{opacity:1;transform:scale(1);transform-origin:0 0}}@keyframes scale-in-tr{0%{opacity:1;transform:scale(0);transform-origin:100% 0}100%{opacity:1;transform:scale(1);transform-origin:100% 0}}@keyframes scale-out-br{0%{opacity:1;transform:scale(1);transform-origin:100% 100%}99%{opacity:1;transform:scale(0.01);transform-origin:100% 100%}100%{display:none;opacity:1;transform:scale(0);transform-origin:100% 100%}}@keyframes scale-out-bl{0%{opacity:1;transform:scale(1);transform-origin:0 100%}99%{opacity:1;transform:scale(0.01);transform-origin:0 100%}100%{display:none;opacity:1;transform:scale(0);transform-origin:0 100%}}@keyframes popup-suggestion{0%{box-shadow:0 0 0 0 rgba(0,0,0,0),0 0 0 0 rgba(0,0,0,0);transform:scaleY(0.4);transform-origin:0 100%}100%{box-shadow:0 -12px 15px -12px rgba(0,0,0,.35);transform:scaleY(1);transform-origin:0 100%}}@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}@keyframes dialog-in{0%{transform:translateY(-20px);opacity:0}100%{transform:translateY(0);opacity:1}}@keyframes dialog-out{0%{transform:translateY(0);opacity:1}100%{transform:translateY(-20px);opacity:0}}@keyframes typing-cue{0%{opacity:1}30%{opacity:.1}50%{opacity:1}100%{opacity:.1}}@keyframes webview-slide-out-bottom{0%{transform:translateY(0);opacity:1}95%{opacity:1}100%{transform:translateY(100%);opacity:0}}@keyframes webview-slide-in-bottom{0%{transform:translateY(100%);opacity:0}1%{opacity:1}100%{transform:translateY(0%);opacity:1}}@keyframes cancel-button-entrance{0%{transform:translateZ(-64px);opacity:0}100%{transform:translateZ(0);opacity:1}}@keyframes cancel-button-exit{0%{transform:translateZ(0);opacity:1}100%{transform:translateZ(-64px);opacity:0}}@keyframes icon-enter{0%{opacity:.4;transform:rotateY(-85deg)}100%{opacity:1;transform:rotateY(0)}}@keyframes icon-exit{0%{opacity:1;transform:rotateY(0)}100%{opacity:.4;transform:rotateY(-85deg)}}.flex{display:flex;justify-content:space-between;align-items:center}.col{flex-direction:column}.none{display:none !important}.wrapper{--color-branding: #c0533f;--color-branding-light: #ca4d3c;--color-branding-dark: #9b382a;--color-launch-icon-background: #c0533f;--color-text: #161513;--color-text-light: #161513;--color-header-background: #F1EFED;--color-header-button-fill: #161513;--color-header-text: #161513;--color-header-button-background-hover: rgba(22, 21, 19, 0.04);--color-header-button-fill-hover: #161513;--color-conversation-background: #F5F4F2;--color-timestamp: rgba(22, 21, 19, 0.65);--color-border: #1615131F;--color-typing-indicator: #161513;--color-agent-initials: #FFFFFF;--color-agent-avatar-background: #A890B6;--color-agent-name: rgba(22, 21, 19, 0.65);--color-bot-message-background: #FFFFFF;--color-bot-text: #161513;--color-user-message-background: #E4E1DD;--color-user-text: #161513;--color-error-message-background: #FFF8F7;--color-error-border: #DC5C5E;--color-error-title: #D63B25;--color-error-text: #161513;--color-card-background: #FFFFFF;--color-card-nav-button: #FFF;--color-card-nav-button-focus: #FBF9F8;--color-card-nav-button-hover: #FBF9F8;--color-actions-background: #fff;--color-actions-background-focus: #fff;--color-actions-background-hover: rgba(22, 21, 19, 0.04);--color-actions-border: rgba(22, 21, 19, 0.5);--color-actions-outline-focus: rgb(22, 21, 19);--color-actions-text: #161513;--color-actions-text-focus: #161513;--color-actions-text-hover: #161513;--color-global-actions-background: transparent;--color-global-actions-background-focus: transparent;--color-global-actions-background-hover: rgba(22, 21, 19, 0.04);--color-global-actions-border: rgba(22, 21, 19, 0.5);--color-global-actions-text: #161513;--color-global-actions-text-focus: #161513;--color-global-actions-text-hover: #161513;--color-primary-actions-background: rgb(49, 45, 42);--color-primary-actions-background-focus: rgb(49, 45, 42);--color-primary-actions-background-hover: rgb(49, 45, 42) linear-gradient(rgb(58, 54, 50), rgb(58, 54, 50));--color-primary-actions-border: transparent;--color-primary-actions-text: #fff;--color-primary-actions-text-focus: #fff;--color-primary-actions-text-hover: #fff;--color-danger-actions-background: rgb(214, 59, 37);--color-danger-actions-background-focus: rgb(214, 59, 37);--color-danger-actions-background-hover: rgb(214, 59, 37) linear-gradient(rgb(195, 53, 34), rgb(195, 53, 34));--color-danger-actions-border: transparent;--color-danger-actions-text: #fff;--color-danger-actions-text-focus: #fff;--color-danger-actions-text-hover: #fff;--color-links: #c0533f;--color-user-links: #c0533f;--color-rating-star: #ececec;--color-rating-star-fill: #f0cc71;--color-horizontal-rule-background: #cbc5bf;--color-attachment-placeholder: #e3e1dc;--color-attachment-footer: #fff;--color-attachment-text: #161513;--color-footer-form-label: rgba(22, 21, 19, 0.65);--color-footer-background: #fff;--color-footer-button-fill: #161513;--color-footer-button-background-hover: rgba(22, 21, 19, 0.04);--color-footer-button-fill-hover: #161513;--color-input-background: #fff;--color-input-border: #fff;--color-input-text: #161513;--color-recognition-view-text: #fff;--color-visualizer: #161513;--color-visualizer-container-background: #fff;--color-notification-badge-background: #312d2a;--color-notification-badge-text: #fff;--color-popup-background: #fff;--color-popup-text: #161513;--color-popup-button-background: #fff;--color-popup-button-text: #161513;--color-popup-horizontal-rule: #cbc5bf;--color-popup-item-background-hover: rgba(22, 21, 19, 0.04);--color-table-header-background: #f1efec;--color-table-header-text: #161513;--color-table-title-separator: #b3b1af;--color-table-background: #fff;--color-table-text: #161513;--color-table-separator: rgba(22, 21, 19, 0.1);--color-table-row-background-hover: rgba(22, 21, 19, 0.04);--color-table-actions-background: transparent;--color-table-actions-background-focus: transparent;--color-table-actions-background-hover: rgba(22, 21, 19, 0.04);--color-table-actions-border: rgba(22, 21, 19, 0.5);--color-table-actions-text: #161513;--color-table-actions-text-focus: #161513;--color-table-actions-text-hover: #161513;--color-form-header-background: #f1efec;--color-form-header-text: #161513;--color-form-background: #fff;--color-form-text: #161513;--color-form-input-background: #fff;--color-form-input-border: rgba(22, 21, 19, 0.5);--color-form-input-border-focus: rgb(14, 114, 151);--color-form-input-text: #161513;--color-form-label: rgba(22, 21, 19, 0.65);--color-form-required-tip: rgba(22, 21, 19, 0.65);--color-form-error: rgba(179, 49, 31);--color-form-error-text: rgba(22, 21, 19, 0.65);--color-form-actions-background: transparent;--color-form-actions-background-focus: transparent;--color-form-actions-background-hover: rgba(22, 21, 19, 0.04);--color-form-actions-border: rgba(22, 21, 19, 0.5);--color-form-actions-text: #161513;--color-form-actions-text-focus: #161513;--color-form-actions-text-hover: #161513;--color-primary-form-actions-background: rgb(49, 45, 42);--color-primary-form-actions-background-focus: rgb(49, 45, 42);--color-primary-form-actions-background-hover: rgb(49, 45, 42) linear-gradient(rgb(58, 54, 50), rgb(58, 54, 50));--color-primary-form-actions-border: transparent;--color-primary-form-actions-text: #fff;--color-primary-form-actions-text-focus: #fff;--color-primary-form-actions-text-hover: #fff;--color-danger-form-actions-background: rgb(214, 59, 37);--color-danger-form-actions-background-focus: rgb(214, 59, 37);--color-danger-form-actions-background-hover: rgb(214, 59, 37) linear-gradient(rgb(195, 53, 34), rgb(195, 53, 34));--color-danger-form-actions-border: transparent;--color-danger-form-actions-text: #fff;--color-danger-form-actions-text-focus: #fff;--color-danger-form-actions-text-hover: #fff;--bubble-max-width: 680px;--width-full-screen: 375px;--widget-max-height: calc(100vh - 60px);--position-top: 0;--position-left: 0;--position-right: 20px;--position-bottom: 20px;--font-family: "Oracle Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", sans-serif;--color-search-bar-separator: rgba(22, 21, 19, .12);position:fixed;box-sizing:border-box;text-transform:none;z-index:10000;color:var(--color-text);font-size:13.75px;line-height:16px;font-family:var(--font-family);-webkit-font-smoothing:antialiased}.wrapper.classic{--color-branding: #025e7e;--color-branding-light: #0e7295;--color-branding-dark: #06485f;--color-launch-icon-background: #025e7e;--color-text: #161513;--color-text-light: #3a3631;--color-header-background: #025e7e;--color-header-button-fill: #fff;--color-header-button-fill-hover: #fff;--color-header-text: #fff;--color-conversation-background: #fff;--color-timestamp: #5b5652;--color-border: #1615131F;--color-typing-indicator: #227e9e;--color-bot-message-background: #e5f1ff;--color-user-message-background: #ececec;--color-card-background: #e5f1ff;--color-card-nav-button: #4190ac;--color-card-nav-button-focus: #5fa2ba;--color-card-nav-button-hover: #0e7295;--color-actions-background: transparent;--color-actions-background-focus: transparent;--color-actions-background-hover: rgba(14, 114, 149, 0.04);--color-actions-border: rgb(14, 114, 149);--color-actions-text: rgb(14, 114, 149);--color-actions-text-focus: rgb(14, 114, 149);--color-actions-text-hover: rgb(14, 114, 149);--color-global-actions-background: #fff;--color-global-actions-background-focus: #fff;--color-global-actions-background-hover: rgba(14, 114, 149, 0.04);--color-global-actions-border: rgb(14, 114, 149);--color-global-actions-text: rgb(14, 114, 149);--color-global-actions-text-focus: rgb(14, 114, 149);--color-global-actions-text-hover: rgb(14, 114, 149);--color-primary-actions-background: rgb(14, 114, 149);--color-primary-actions-background-focus: rgb(14, 114, 149);--color-primary-actions-background-hover: rgba(14, 114, 149, 0.95);--color-links: #0e7295;--color-user-links: #0e7295;--color-agent-name: #5b5652;--color-attachment-footer: #e5f1ff;--color-footer-background: #fff;--color-footer-button-fill: #161513;--color-footer-button-fill-hover: #025e7e;--color-visualizer: #025e7e;--color-primary-form-actions-background: rgb(14, 114, 149);--color-primary-form-actions-background-focus: rgb(14, 114, 149);--color-primary-form-actions-background-hover: rgba(14, 114, 149, 0.95);--color-notification-badge-background: #9a0007;--color-notification-badge-text: #fff;--color-popup-button-text: #025e7e}.wrapper.redwood-dark{--color-branding: #c0533f;--color-branding-light: #ca4d3c;--color-branding-dark: #9b382a;--color-launch-icon-background: #c0533f;--color-text: #161513;--color-text-light: #fcfbfa;--color-header-background: #201e1c;--color-header-button-fill: #fff;--color-header-button-fill-hover: #fff;--color-header-button-background-hover: rgba(255, 255, 255, 0.04);--color-header-text: #fff;--color-conversation-background: #3a3631;--color-timestamp: #fcfbfa;--color-border: #FCFBFA1F;--color-typing-indicator: #fff;--color-bot-message-background: #655f5c;--color-bot-text: #fff;--color-user-message-background: #fff;--color-user-text: #161513;--color-card-background: #655f5c;--color-card-nav-button: #d5b364;--color-card-nav-button-focus: #f7e0a1;--color-card-nav-button-hover: #b39554;--color-actions-background: #655f5c;--color-actions-background-focus: #655f5c;--color-actions-background-hover: rgba(22, 21, 19, 0.3);--color-actions-border: #fff;--color-actions-text: #fff;--color-actions-text-focus: #fff;--color-actions-text-hover: #fff;--color-global-actions-background: #3a3631;--color-global-actions-background-focus: #3a3631;--color-global-actions-background-hover: rgba(22, 21, 19, 0.3);--color-global-actions-border: #fff;--color-global-actions-text: #fff;--color-global-actions-text-focus: #fff;--color-global-actions-text-hover: #fff;--color-primary-actions-background: #fff;--color-primary-actions-background-focus: #fff;--color-primary-actions-background-hover: #fff linear-gradient(rgb(251, 249, 248), rgb(251, 249, 248));--color-primary-actions-text: #161513;--color-primary-actions-text-focus: #161513;--color-primary-actions-text-hover: #161513;--color-danger-actions-background-focus: rgb(214, 59, 37);--color-danger-actions-background-hover: rgb(214, 59, 37) linear-gradient(rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.08));--color-links: #f7e0a1;--color-user-links: #c0533f;--color-agent-name: #fcfbfa;--color-footer-form-label: #fcfbfa;--color-footer-background: #fff;--color-footer-button-fill: #161513;--color-input-background: #fff;--color-input-text: #161513;--color-recognition-view-text: #fff;--color-visualizer-container-background: #fff;--color-notification-badge-background: #312d2a;--color-notification-badge-text: #fff;--color-popup-button-text: #201e1c}.wrapper:not(.embedded):not(.contextual-widget):not(.search-bar-widget-wrapper){bottom:var(--position-bottom);left:var(--position-left);top:var(--position-top);right:var(--position-right)}.wrapper *{box-sizing:border-box}.wrapper .widget-button{position:relative;max-width:100%;padding:9px 16px;margin:0 0 8px;min-height:36px;line-height:16px;font-size:13.75px;font-weight:600;font-family:inherit;border-radius:4px;border-width:thin;border-style:solid;cursor:pointer;overflow:hidden;flex-shrink:0;word-break:normal;overflow-wrap:anywhere}.wrapper .widget-button:disabled{opacity:.5;cursor:not-allowed}.wrapper .widget-button.icon{width:36px;height:36px;padding:8px;margin:0;margin-inline-start:4px;border:none;border-radius:4px;color:var(--color-text);background-color:rgba(0,0,0,0);justify-content:center}.wrapper .widget-button.icon.with-label{width:auto;max-width:200px}.wrapper .widget-button.icon.with-label svg,.wrapper .widget-button.icon.with-label img{margin-right:4px}.wrapper .widget-button.icon.label-only{width:auto;max-width:200px}.wrapper .widget-button.icon.label-only svg,.wrapper .widget-button.icon.label-only img{display:none}.wrapper .widget-button:not(:disabled):focus{outline:1px dotted var(--color-actions-outline-focus);outline-offset:1px}.wrapper .widget-button svg,.wrapper .widget-button img{width:20px;height:20px;flex-shrink:0}.wrapper .button{position:absolute;right:0;bottom:0;height:48px;width:48px;max-width:unset;padding:0;margin:0;border:none;background-position:center center;background-repeat:no-repeat;cursor:pointer;justify-content:center;align-items:center;z-index:10000;color:var(--color-text);background-color:var(--color-launch-icon-background);border-radius:0;overflow:visible}.wrapper .button svg,.wrapper .button img{height:unset;width:unset;max-width:100%;max-height:100%}.wrapper .button:not(:disabled):hover,.wrapper .button:not(:disabled):focus,.wrapper .button:not(:disabled):active{background-color:var(--color-launch-icon-background)}@media screen and (min-width: 769px){.wrapper .button{height:64px;width:64px}}.wrapper .dialog-wrapper{position:absolute;top:0;left:0;right:0;width:100%;height:100%}.wrapper .dialog-wrapper .dialog-backdrop{position:absolute;background:rgba(0,0,0,.2);height:100%;width:100%;z-index:5}.wrapper .dialog-wrapper .dialog{box-shadow:rgba(0,0,0,.16) 0px 4px 8px 0px;border-radius:6px;position:relative;max-width:450px;min-height:48px;max-height:60%;top:30%;left:0;right:0;padding:8px 16px;margin:8px auto;width:calc(100% - 16px);z-index:5;animation:dialog-in .2s cubic-bezier(0.22, 0.45, 0.42, 0.92) both;background-color:var(--color-popup-background);overflow-y:auto}.wrapper .dialog-wrapper .dialog.dialog-out{animation:dialog-out .2s cubic-bezier(0.5, 0.07, 0.68, 0.48) both}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper{margin:16px 0}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-icon{width:20px;height:20px;max-width:20px;max-height:20px;margin-inline-end:8px}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-icon img,.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-icon svg{max-width:20px;max-height:20px}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-content{line-height:1.4;margin-inline-end:28px}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-content .dialog-title{font-family:var(--font-family);font-size:18px;font-weight:bold;color:var(--color-popup-text);word-break:normal;overflow-wrap:anywhere}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-content .dialog-description{color:var(--color-popup-text);opacity:.6;font-size:13px;margin-top:8px}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-label{color:var(--color-popup-text);font-size:large}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-input{font-size:medium;min-height:36px;width:100%;margin:0 0 10px 0;padding:10px;color:var(--color-form-input-text);border:1px solid var(--color-form-input-border);border-radius:4px}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-input:focus{border-color:var(--color-form-input-border-focus);box-shadow:0 0 0 1px var(--color-form-input-border-focus) inset;outline:1px solid rgba(0,0,0,0)}.wrapper .dialog-wrapper .dialog .dialog-icon-content-wrapper .dialog-input:invalid{border:1px solid var(--color-form-error)}.wrapper .dialog-wrapper .dialog .dialog-close-button{margin-inline-start:0}.wrapper .dialog-wrapper .dialog .action-wrapper{width:100%;margin:16px 0 6px;gap:16px}.wrapper .dialog-wrapper .dialog .action-wrapper .popup-action{background-color:var(--color-popup-button-background);border-color:var(--color-popup-button-text);color:var(--color-popup-button-text);border-style:solid;margin:0;height:34px;justify-content:center;flex:1 0 auto}.wrapper .dialog-wrapper .dialog .action-wrapper .popup-action:hover{background-color:var(--color-footer-button-background-hover)}.wrapper .dialog-wrapper .dialog .action-wrapper .popup-action:last-child{margin:0}.wrapper .dialog-wrapper .dialog .action-wrapper .popup-action.filled{background-color:var(--color-popup-button-text);color:var(--color-popup-button-background)}.wrapper .dialog-wrapper .dialog .action-wrapper .popup-action.filled:hover{opacity:.9}.wrapper .dialog-wrapper.modeless{top:56px;height:auto}.wrapper .dialog-wrapper.modeless .dialog{gap:16px;top:0}.wrapper .dialog-wrapper.modeless .dialog .dialog-icon-content-wrapper{margin:0}.wrapper .dialog-wrapper.modeless .dialog .dialog-icon-content-wrapper .dialog-content{margin:0}.wrapper .dialog-wrapper.modeless .dialog .dialog-icon-content-wrapper .dialog-content .dialog-title{font-size:16px;line-height:1.3333;font-weight:normal}.wrapper .header{height:56px;padding:0 8px;background-color:var(--color-header-background);color:var(--color-header-text)}.wrapper .header .logo{flex:0 0 auto;max-width:100px;height:36px;max-height:36px;overflow:hidden;padding:0}.wrapper .header .header-info-wrapper{flex-direction:column;flex-wrap:nowrap;width:100%;min-width:0;padding:0;margin:0 8px}.wrapper .header .header-info-wrapper .title{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:1.125em;font-weight:700}.wrapper .header .header-info-wrapper .subtitle{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.wrapper .header .header-info-wrapper .connection-status{font-weight:bold;font-size:10px;justify-content:center;padding:0;margin:0;text-transform:uppercase;text-overflow:ellipsis;white-space:nowrap;overflow:hidden}.wrapper .header .header-gap{flex:auto}.wrapper .header-actions{flex:1 0 auto;justify-content:flex-end;flex-direction:inherit}.wrapper .header-button svg>path{fill:var(--color-header-button-fill)}.wrapper .header-button:not(:disabled):hover{background-color:var(--color-header-button-background-hover)}.wrapper .header-button:not(:disabled):hover svg>path{fill:var(--color-header-button-fill-hover)}.wrapper .footer{max-width:100%;padding:0;position:relative;background-color:var(--color-footer-background);z-index:3;box-shadow:0px -1px 4px 0px rgba(0,0,0,.1019607843);border-top:1px solid rgba(22,21,19,.1)}.wrapper .footer .footer-mode-keyboard{margin:5px;background-color:var(--color-input-background);color:var(--color-input-text);border:1px solid var(--color-input-border);border-radius:6px}.wrapper .footer .footer-mode-voice{height:60px;padding:14px 0;background:var(--color-visualizer-container-background);justify-content:center}.wrapper .footer .footer-mode-voice .footer-visualizer-wrapper{max-width:296px;height:32px}.wrapper .footer .footer-logo{flex:0 0 auto;max-width:100px;max-height:36px;overflow:hidden;padding:0}.wrapper .footer.mode-keyboard .button-switch-kbd{display:none}.wrapper .footer.mode-keyboard .footer-mode-voice{display:none}.wrapper .footer.mode-voice .button-switch-voice{display:none}.wrapper .user-input{flex:1 1 auto;min-height:44px;min-width:0;padding:14px 4px 14px 10px;margin:0;font-size:16px;font-family:inherit;text-align:start;line-height:16px;outline:1px solid rgba(0,0,0,0);resize:none;border:none;background-color:rgba(0,0,0,0);color:var(--color-input-text)}.wrapper .user-input:focus,.wrapper .user-input:focus-visible{outline:1px solid rgba(22,21,19,0)}.wrapper .footer-actions{margin-inline-end:2px}.wrapper .footer-button.button-send{background-color:var(--color-footer-button-fill);border-radius:50%}.wrapper .footer-button.button-send svg>path{fill:var(--color-input-background)}.wrapper .footer-button.button-send:not(:disabled):hover{background-color:var(--color-footer-button-fill-hover)}.wrapper .footer-button.button-send:not(:disabled):hover svg>path{fill:var(--color-input-background)}.wrapper .footer-button svg>path{fill:var(--color-footer-button-fill)}.wrapper .footer-button:not(:disabled):hover{background-color:var(--color-footer-button-background-hover)}.wrapper .footer-button:not(:disabled):hover svg>path{fill:var(--color-footer-button-fill-hover)}.wrapper .autocomplete-items{position:absolute;bottom:56px;width:100%;max-height:280px;overflow-y:auto;background-color:var(--color-input-background);box-shadow:0px -1px 4px 0px rgba(0,0,0,.1019607843);margin:0 -5px;padding:0}.wrapper .autocomplete-items .autocomplete-item{align-items:center;display:flex;margin:0;min-height:40px;padding:8px 16px;cursor:pointer}.wrapper .autocomplete-items .autocomplete-item:hover,.wrapper .autocomplete-items .autocomplete-item.autocomplete-active{background-color:var(--color-card-nav-button-hover)}.wrapper .autocomplete-items .autocomplete-item:first-of-type{margin-top:8px}.wrapper .autocomplete-items .autocomplete-item:last-of-type{margin-bottom:8px}.wrapper .autocomplete-items .autocomplete-item .strong{font-weight:700}.wrapper .autocomplete-items .autocomplete-item::marker{content:none}.wrapper .conversation{display:flex;flex:1;-webkit-box-orient:vertical;-webkit-box-direction:normal;flex-direction:column;overflow-x:hidden;overflow-y:auto;position:relative;scroll-behavior:smooth;width:100%;padding:16px}.wrapper .conversation .conversation-pane .message-date,.wrapper .conversation .conversation-pane .relative-timestamp{font-size:12px;margin:8px 0 8px;color:var(--color-timestamp);text-align:start}.wrapper .conversation .conversation-pane .message-date.right,.wrapper .conversation .conversation-pane .relative-timestamp.right{text-align:end}.wrapper .conversation .conversation-pane.bot-icon .message.card-message-horizontal{margin-inline-start:-52px}.wrapper .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-header,.wrapper .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-footer,.wrapper .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-global-actions{margin-inline-start:52px}.wrapper .conversation .conversation-pane.bot-icon .message.card-message-horizontal .card-message-content .card-message-cards{padding-inline-start:52px}.wrapper .conversation .conversation-pane.bot-icon .relative-timestamp.left{margin-inline-start:36px}.wrapper .conversation .conversation-pane.user-icon .relative-timestamp.right{margin-inline-end:36px}.wrapper .conversation .conversation-pane.bot-icon .message-block .messages-wrapper,.wrapper .conversation .conversation-pane.user-icon .message-block .messages-wrapper{max-width:calc(.9*(100% - 36px))}.wrapper .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions,.wrapper .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions{max-width:calc(.9*(100% - 68px))}.wrapper .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper{max-width:calc(.9*(100% - 72px))}.wrapper .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions{max-width:calc(.9*(100% - 104px))}.wrapper .conversation .cancel-response-button{background-color:var(--color-branding);border-radius:10000px;bottom:0;box-shadow:0 0 4px 0 rgba(0,0,0,.25);height:36px;inset-inline-start:100%;position:sticky;width:36px;z-index:100;animation:cancel-button-entrance .25s ease-in forwards;transition:all .25s ease-in-out}.wrapper [dir=rtl] .conversation .cancel-response-button{inset-inline-start:calc(100% - 36px)}.wrapper .conversation .cancel-response-button .cancel-response-button-icon path{fill:#fff}.wrapper .conversation .cancel-response-button:hover{background-color:var(--color-branding-light);box-shadow:0 0 4px 0 rgba(0,0,0,.25)}.wrapper .conversation .cancel-response-button:active{background-color:var(--color-branding-dark);box-shadow:0 0 4px 0 rgba(0,0,0,.25)}.wrapper .conversation .cancel-response-button:focus{outline:none;box-shadow:0 0 4px 0 rgba(0,0,0,.25)}.wrapper .conversation .cancel-response-button:focus:not(:focus-visible){box-shadow:0 0 4px 0 rgba(0,0,0,.25)}.wrapper .conversation .cancel-response-button.hide{animation:cancel-button-exit .2s ease-out forwards}.wrapper .timestamp-container{display:inline-block;position:relative;text-align:center;width:100%}.wrapper .timestamp-container .timestamp-header{background-color:var(--color-conversation-background);color:var(--color-timestamp);display:inline-block;font-size:12px;font-weight:700;padding:0 8px;margin:16px 0;position:relative;text-align:center;text-transform:capitalize;z-index:1}.wrapper .timestamp-container .conversation-separator{border:none;border-top:1px solid var(--color-border);position:absolute;margin:0;top:50%;width:100%}.wrapper .hr{margin:24px 0;font-size:12px;color:var(--color-horizontal-rule-background)}.wrapper .hr:before{content:"";background-color:var(--color-horizontal-rule-background);height:1px;flex-grow:1;margin-inline-end:10px}.wrapper .hr:after{content:"";background-color:var(--color-horizontal-rule-background);height:1px;flex-grow:1;margin-inline-start:10px}.wrapper .card-actions,.wrapper .form-actions,.wrapper .message-actions,.wrapper .message-global-actions{margin-top:6px;display:flex;align-items:flex-start;justify-content:flex-start;flex-wrap:wrap}.wrapper .card-actions.form-message-actions-col,.wrapper .form-actions.form-message-actions-col,.wrapper .message-actions.form-message-actions-col,.wrapper .message-global-actions.form-message-actions-col{flex-basis:100%;max-width:100%}.wrapper .card-actions:not(.col) .action-postback,.wrapper .form-actions:not(.col) .action-postback,.wrapper .message-actions:not(.col) .action-postback,.wrapper .message-global-actions:not(.col) .action-postback{margin-inline-end:8px}.wrapper .card-actions:not(.col) .action-postback:last-child,.wrapper .form-actions:not(.col) .action-postback:last-child,.wrapper .message-actions:not(.col) .action-postback:last-child,.wrapper .message-global-actions:not(.col) .action-postback:last-child{margin-inline-end:0}.wrapper .action-postback{background:var(--color-actions-background);border-color:var(--color-actions-border);color:var(--color-actions-text);display:flex;flex-direction:row;gap:10px;text-align:start}.wrapper .action-postback:not(:disabled):hover{color:var(--color-actions-text-hover);background-color:var(--color-actions-background-hover)}.wrapper .action-postback:not(:disabled):hover svg>path{fill:var(--color-actions-text-hover)}.wrapper .action-postback:not(:disabled):focus,.wrapper .action-postback:not(:disabled):active{background-color:var(--color-actions-background-focus);color:var(--color-actions-text-focus)}.wrapper .action-postback:not(:disabled):focus svg>path,.wrapper .action-postback:not(:disabled):active svg>path{fill:var(--color-actions-text-focus)}.wrapper .action-postback.primary{background:var(--color-primary-actions-background);color:var(--color-primary-actions-text);border:var(--color-primary-actions-border)}.wrapper .action-postback.primary:not(:disabled):hover{background:var(--color-primary-actions-background-hover);color:var(--color-primary-actions-text-hover)}.wrapper .action-postback.primary:not(:disabled):hover svg>path{fill:var(--color-primary-actions-text-hover)}.wrapper .action-postback.primary:not(:disabled):focus,.wrapper .action-postback.primary:not(:disabled):active{background:var(--color-primary-actions-background-focus);color:var(--color-primary-actions-text-focus)}.wrapper .action-postback.primary:not(:disabled):focus svg>path,.wrapper .action-postback.primary:not(:disabled):active svg>path{fill:var(--color-primary-actions-text-focus)}.wrapper .action-postback.danger{background:var(--color-danger-actions-background);color:var(--color-danger-actions-text);border:var(--color-danger-actions-border)}.wrapper .action-postback.danger:not(:disabled):hover{background:var(--color-danger-actions-background-hover);color:var(--color-danger-actions-text-hover)}.wrapper .action-postback.danger:not(:disabled):hover svg>path{fill:var(--color-danger-actions-text-hover)}.wrapper .action-postback.danger:not(:disabled):focus,.wrapper .action-postback.danger:not(:disabled):active{background:var(--color-danger-actions-background-focus);color:var(--color-danger-actions-text-focus)}.wrapper .action-postback.danger:not(:disabled):focus svg>path,.wrapper .action-postback.danger:not(:disabled):active svg>path{fill:var(--color-danger-actions-text-focus)}.wrapper .action-postback.display-link{outline:1px solid rgba(0,0,0,0);border:none;min-height:unset;background:rgba(0,0,0,0) !important;padding:0}.wrapper .action-postback.display-link:hover{text-decoration:underline}.wrapper .action-postback.c2k-action{border-radius:0;color:#227e9e !important;border:none;padding:0;min-height:unset;font-size:16px;background:rgba(0,0,0,0) !important;margin-bottom:0}.wrapper .action-postback .icon-enter{animation:icon-enter .2s ease-in}.wrapper .action-postback .icon-exit{animation:icon-exit .2s ease-out}.wrapper .message-global-actions{margin-top:8px}.wrapper .message-global-actions.stars{display:block}.wrapper .message-global-actions .widget-button{background:var(--color-global-actions-background);color:var(--color-global-actions-text);border-color:var(--color-global-actions-border)}.wrapper .message-global-actions .widget-button:not(:disabled):hover{background-color:var(--color-global-actions-background-hover);color:var(--color-global-actions-text-hover)}.wrapper .message-global-actions .widget-button:not(:disabled):hover svg>path{fill:var(--color-global-actions-text-hover)}.wrapper .message-global-actions .widget-button:not(:disabled):focus,.wrapper .message-global-actions .widget-button:not(:disabled):active{background-color:var(--color-global-actions-background-focus);color:var(--color-global-actions-text-focus)}.wrapper .message-global-actions .widget-button:not(:disabled):focus svg>path,.wrapper .message-global-actions .widget-button:not(:disabled):active svg>path{fill:var(--color-global-actions-text-focus)}.wrapper .message-bubble{position:relative;display:flex;flex-direction:column;align-items:flex-start;margin:0;padding:6px 16px;color:var(--color-bot-text);background:var(--color-bot-message-background);min-height:28px;line-height:16px;overflow:hidden;max-width:100%;border-radius:2px 10px 10px 2px;margin-top:2px;word-break:normal;overflow-wrap:anywhere}.wrapper .message-bubble>*{width:100%}.wrapper .message-bubble.before-card{border-radius:2px 10px 10px 10px}.wrapper .message-bubble .video-wrapper{max-width:100%}.wrapper .message-bubble.error{background-color:var(--color-error-message-background);color:var(--color-error-text);border:1px dashed var(--color-error-border)}.wrapper .message-bubble.error .message-icon path{fill:var(--color-error-title)}.wrapper .message-bubble.error .message-title{color:var(--color-error-title)}.wrapper .message-bubble span.highlight{background-color:rgba(143,191,208,.4)}.wrapper .message-bubble .message-with-icon{display:flex;align-items:flex-start;justify-content:space-between}.wrapper .message-bubble .message-with-icon .message-icon{width:24px;height:24px;align-items:center;margin-inline-end:16px}.wrapper .message-bubble .message-with-icon .message-text{word-break:normal;overflow-wrap:anywhere}.wrapper .message-bubble.message-header{margin-bottom:2px}.wrapper .message-bubble.message-footer{margin-top:2px}.wrapper .message-bubble .message-user-postback>img{max-height:32px;max-width:32px}.wrapper .message-bubble .message-bubble{border:0;margin-top:8px;padding:0}.wrapper .message-bubble .message-bubble:not(:first-child){margin-top:8px}.wrapper .messages-wrapper{max-width:90%;align-items:flex-start}.wrapper .messages-wrapper .agent-name{position:relative;bottom:3px;max-width:111.1111111111%;height:16px;font-size:12px;line-height:16px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--color-agent-name)}.wrapper .messages-wrapper .screen-reader-only{height:1px;left:-20000px;overflow:hidden;position:absolute;top:auto;width:1px}.wrapper .messages-wrapper .message-list{width:100%;align-items:flex-start}.wrapper .message{width:100%;white-space:pre-wrap}.wrapper .message .embeddedAction{padding:2px 6px;border-radius:4px;cursor:pointer;display:inline-block;font-size:12px;font-weight:600;height:20px;line-height:16px;border:1px solid rgba(122,115,110,.2509803922)}.wrapper .message .embeddedAction.display-link{color:var(--color-links);padding:2px 0;outline:1px solid rgba(0,0,0,0);border:none}.wrapper .message .embeddedAction.display-link:hover{text-decoration:underline}.wrapper .message .embeddedAction.display-icon{padding:0;outline:1px solid rgba(0,0,0,0);border:none}.wrapper .message .action-wrapper{display:flex;flex-direction:column;position:relative}.wrapper .message .action-wrapper .widget-button:not(:disabled):hover+div>.tooltip{display:block;position:absolute;background-color:var(--color-bot-message-background);max-width:296px;border-radius:2px;box-shadow:0px 1px 4px 0px rgba(0,0,0,.1215686275);padding:8px;z-index:3;font-size:13px;font-weight:400;inset-inline-start:-16px;line-height:20px;margin-top:-4px;word-break:normal;overflow-wrap:anywhere}.wrapper .message a{color:var(--color-links)}.wrapper .message b{font-weight:700}.wrapper .message .widget-button.anchor-btn{padding:0}.wrapper .message .widget-button.anchor-btn a{display:block;text-decoration:inherit;color:inherit;padding:10px 20px}.wrapper .message .widget-button:last-child{margin-bottom:0}.wrapper .message .message-wrapper{display:flex;align-items:flex-start;flex-direction:column;width:100%;max-width:100%}.wrapper .message:first-child .message-bubble:not(.message-footer){margin-top:0}.wrapper .message:first-child .message-bubble:not(.message-footer) .message-bubble{margin-top:8px}.wrapper .message:first-child .card-message-content:first-child .card-message-cards{margin-top:0}.wrapper .message:last-child .message-bubble:last-child{border-radius:2px 10px 10px 10px}.wrapper .message:last-child .message-bubble:last-child .message-bubble{border-radius:0}.wrapper .message:last-child .message-bubble:last-child.edit-form-message .form-message-header{border-radius:1px 9px 0 0}.wrapper .message:last-child .message-bubble:last-child.edit-form-message .form-message-item{border-radius:1px 9px 9px 9px}.wrapper .message:last-child .card-message-content:last-child .card-message-cards{margin-bottom:-8px}.wrapper .message.card-message-horizontal{margin-inline-start:-16px;width:calc(var(--width-full-screen) - 12px)}.wrapper .message.card-message-horizontal .message-header,.wrapper .message.card-message-horizontal .message-footer,.wrapper .message.card-message-horizontal .message-global-actions{margin-inline-start:16px;max-width:calc(.9*(100% - 28px))}.wrapper .message.card-message-horizontal .message-header{border-radius:2px 10px 10px 10px}.wrapper .message.card-message-horizontal .card-message-cards{flex-direction:row;overflow-x:auto;padding-inline-start:16px}.wrapper .message.card-message-horizontal .card{border:1px solid rgba(22,21,19,.12);box-shadow:0px 1px 4px 0px rgba(0,0,0,.12);margin-inline-end:8px}.wrapper .message.card-message-horizontal .next-wrapper,.wrapper .message.card-message-horizontal .prev-wrapper{position:absolute;height:100%;top:0;width:52px;z-index:1}.wrapper .message.card-message-horizontal .next-wrapper{inset-inline-end:0;background:linear-gradient(90deg, rgba(255, 255, 255, 0), var(--color-conversation-background) 60%)}.wrapper .message.card-message-horizontal .prev-wrapper{inset-inline-start:0;background:linear-gradient(90deg, var(--color-conversation-background) 40%, rgba(255, 255, 255, 0))}.wrapper [dir=rtl] .message.card-message-horizontal .next-wrapper{background:linear-gradient(90deg, var(--color-conversation-background) 40%, rgba(255, 255, 255, 0))}.wrapper [dir=rtl] .message.card-message-horizontal .prev-wrapper{background:linear-gradient(90deg, rgba(255, 255, 255, 0), var(--color-conversation-background) 60%)}.wrapper [dir=rtl] .message.card-message-horizontal .next,.wrapper [dir=rtl] .message.card-message-horizontal .previous{transform:rotate(180deg)}.wrapper .message.card-message-horizontal .next,.wrapper .message.card-message-horizontal .previous{position:absolute;z-index:10;width:36px;height:36px;left:8px;padding:0;overflow:hidden;background-color:var(--color-card-nav-button);border:none;box-shadow:0px 2px 4px rgba(0,0,0,.1);top:calc(50% - 18px);justify-content:center}.wrapper .message.card-message-horizontal .next:hover,.wrapper .message.card-message-horizontal .previous:hover{background-color:var(--color-card-nav-button-hover)}.wrapper .message.card-message-horizontal .next:focus,.wrapper .message.card-message-horizontal .next:active,.wrapper .message.card-message-horizontal .previous:focus,.wrapper .message.card-message-horizontal .previous:active{background-color:var(--color-card-nav-button-focus)}.wrapper .message-block{justify-content:flex-start;align-items:flex-start;margin-bottom:8px}.wrapper .message-block.right{flex-direction:row-reverse}.wrapper .message-block.right .icon-wrapper{margin:unset;margin-inline-start:8px}.wrapper .message-block.right .messages-wrapper{align-items:flex-end}.wrapper .message-block.right .messages-wrapper .message a{color:var(--color-user-links)}.wrapper .message-block.right .messages-wrapper .message .message-wrapper{align-items:flex-end}.wrapper .message-block.right .messages-wrapper .message .message-bubble{border-radius:10px 2px 2px 10px}.wrapper .message-block.right .messages-wrapper .message .message-bubble:not(.error){color:var(--color-user-text);background:var(--color-user-message-background)}.wrapper .message-block.right .messages-wrapper .message:last-child .message-bubble:last-child{border-radius:10px 2px 10px 10px}.wrapper .message-block.right .message-date{text-align:right}.wrapper .icon-wrapper{margin-inline-end:8px;width:28px;height:28px;min-height:28px;min-width:28px;border-radius:4px;overflow:hidden;z-index:1;display:flex;align-items:center;justify-content:center}.wrapper .icon-wrapper.agent-avatar{background:var(--color-agent-avatar-background);margin-top:16px}.wrapper .icon-wrapper .message-icon{height:100%;max-height:100%;max-width:100%;width:100%;color:var(--color-timestamp);overflow:hidden;text-overflow:ellipsis}.wrapper .icon-wrapper .agent-icon{position:relative;min-width:20px;min-height:20px;font-weight:700;font-size:16px;line-height:20px;text-align:center;color:var(--color-agent-initials)}.wrapper .attachment{width:100%}.wrapper .attachment .attachment-placeholder{background-color:var(--color-attachment-placeholder);max-width:calc(100% + 32px);min-width:228px;min-height:88px;max-height:230px;margin:-6px -16px 0;justify-content:center;overflow:hidden}.wrapper .attachment .attachment-placeholder>*{max-width:100%}.wrapper .attachment .attachment-placeholder .attachment-icon{height:48px;width:48px}.wrapper .attachment .attachment-placeholder .attachment-icon svg{height:48px;width:48px}.wrapper .attachment .attachment-placeholder .attachment-icon img{width:100%}.wrapper .attachment .attachment-placeholder .attachment-audio{height:50px;width:100%}.wrapper .attachment .attachment-placeholder .attachment-audio::-webkit-media-controls-enclosure{background-color:rgba(0,0,0,0)}.wrapper .attachment .attachment-placeholder .attachment-video{aspect-ratio:1}.wrapper .attachment .attachment-footer{background-color:var(--color-attachment-footer);color:var(--color-attachment-text);margin:0 -16px -6px;height:50px;padding:16px}.wrapper .attachment .attachment-footer.with-actions{border-bottom:thin solid rgba(22,21,19,.1);margin-bottom:6px}.wrapper .attachment .attachment-footer .attachment-title{flex-grow:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.wrapper .card{width:252px;border-radius:6px;padding:12px 16px;margin-block-end:8px;justify-content:flex-start;flex-shrink:0;color:var(--color-bot-text);background:var(--color-card-background);overflow:hidden}.wrapper .card .card-content{margin-bottom:12px}.wrapper .card .card-image{display:block;width:calc(100% + 32px);margin:-12px -16px 10px;min-height:88px;background-color:var(--color-attachment-placeholder)}.wrapper .card .card-title{margin-bottom:4px;font-weight:700;word-break:normal;overflow-wrap:anywhere}.wrapper .card .card-description{color:var(--color-text-light)}.wrapper .card-message-content{width:100%;position:relative}.wrapper .card-message-content .card-message-cards{width:100%;align-items:stretch;display:flex;scroll-behavior:smooth;overflow-x:visible;flex-direction:column;margin:8px 0 0;scrollbar-width:none}.wrapper .card-message-content .card-message-cards::-webkit-scrollbar{display:none}.wrapper .message-bubble-tabular-message,.wrapper .message-bubble-form-message{width:111%;max-width:unset;border-radius:0 8px 8px 8px;padding:0;background-color:var(--color-table-background);color:var(--color-table-text);border:1px solid var(--color-table-header-background);overflow:hidden}.wrapper .message-bubble-tabular-message .popupContent,.wrapper .message-bubble-form-message .popupContent{max-width:280px;position:absolute;height:auto;border-radius:8px;z-index:3;box-shadow:0px 4px 4px 0px rgba(0,0,0,.1019607843);border:1px solid rgba(22,21,19,.1215686275);background:var(--color-bot-message-background);display:none;inset-inline-start:-4px}.wrapper .message-bubble-tabular-message .results-page-status,.wrapper .message-bubble-form-message .results-page-status{align-items:center;background-color:var(--color-table-background);color:var(--color-table-text);display:flex;flex-direction:row;font-size:13.75px;justify-content:flex-end;line-height:16px;padding:12px 16px;border-top:1px solid var(--color-table-separator)}.wrapper .message-bubble-tabular-message~.message-footer,.wrapper .message-bubble-form-message~.message-footer{margin-top:8px}.wrapper .message-bubble-tabular-message .message-actions .action-postback,.wrapper .message-bubble-tabular-message .table-message-item .action-postback{background:var(--color-table-actions-background);color:var(--color-table-actions-text);border-color:var(--color-table-actions-border)}.wrapper .message-bubble-tabular-message .message-actions .action-postback:not(:disabled):hover,.wrapper .message-bubble-tabular-message .table-message-item .action-postback:not(:disabled):hover{color:var(--color-table-actions-text-hover);background:var(--color-table-actions-background-hover)}.wrapper .message-bubble-tabular-message .message-actions .action-postback:not(:disabled):hover svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback:not(:disabled):hover svg>path{fill:var(--color-table-actions-text-hover)}.wrapper .message-bubble-tabular-message .message-actions .action-postback:not(:disabled):focus,.wrapper .message-bubble-tabular-message .message-actions .action-postback:not(:disabled):active,.wrapper .message-bubble-tabular-message .table-message-item .action-postback:not(:disabled):focus,.wrapper .message-bubble-tabular-message .table-message-item .action-postback:not(:disabled):active{background:var(--color-table-actions-background-focus);color:var(--color-table-actions-text-focus)}.wrapper .message-bubble-tabular-message .message-actions .action-postback:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .message-actions .action-postback:not(:disabled):active svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback:not(:disabled):active svg>path{fill:var(--color-table-actions-text-focus)}.wrapper .message-bubble-tabular-message .message-actions,.wrapper .message-bubble-form-message .message-actions{border-top:1px solid var(--color-table-separator);padding:12px 16px;margin-top:auto}.wrapper .message-bubble-tabular-message .message-actions .action-postback.primary,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.primary,.wrapper .message-bubble-tabular-message .form-actions .action-postback.primary,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.primary,.wrapper .message-bubble-form-message .message-actions .action-postback.primary,.wrapper .message-bubble-form-message .table-message-item .action-postback.primary,.wrapper .message-bubble-form-message .form-actions .action-postback.primary,.wrapper .message-bubble-form-message .form-message-value .action-postback.primary{background:var(--color-primary-form-actions-background);color:var(--color-primary-form-actions-text);border:var(--color-primary-form-actions-border)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.primary:not(:disabled):hover,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.primary:not(:disabled):hover,.wrapper .message-bubble-tabular-message .form-actions .action-postback.primary:not(:disabled):hover,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.primary:not(:disabled):hover,.wrapper .message-bubble-form-message .message-actions .action-postback.primary:not(:disabled):hover,.wrapper .message-bubble-form-message .table-message-item .action-postback.primary:not(:disabled):hover,.wrapper .message-bubble-form-message .form-actions .action-postback.primary:not(:disabled):hover,.wrapper .message-bubble-form-message .form-message-value .action-postback.primary:not(:disabled):hover{background:var(--color-primary-form-actions-background-hover);color:var(--color-primary-form-actions-text-hover)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.primary:not(:disabled):hover svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.primary:not(:disabled):hover svg>path,.wrapper .message-bubble-tabular-message .form-actions .action-postback.primary:not(:disabled):hover svg>path,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.primary:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .message-actions .action-postback.primary:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .table-message-item .action-postback.primary:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .form-actions .action-postback.primary:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .form-message-value .action-postback.primary:not(:disabled):hover svg>path{fill:var(--color-primary-form-actions-text-hover)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-tabular-message .message-actions .action-postback.primary:not(:disabled):active,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.primary:not(:disabled):active,.wrapper .message-bubble-tabular-message .form-actions .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-tabular-message .form-actions .action-postback.primary:not(:disabled):active,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.primary:not(:disabled):active,.wrapper .message-bubble-form-message .message-actions .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-form-message .message-actions .action-postback.primary:not(:disabled):active,.wrapper .message-bubble-form-message .table-message-item .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-form-message .table-message-item .action-postback.primary:not(:disabled):active,.wrapper .message-bubble-form-message .form-actions .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-form-message .form-actions .action-postback.primary:not(:disabled):active,.wrapper .message-bubble-form-message .form-message-value .action-postback.primary:not(:disabled):focus,.wrapper .message-bubble-form-message .form-message-value .action-postback.primary:not(:disabled):active{background:var(--color-primary-form-actions-background-focus);color:var(--color-primary-form-actions-text-focus)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .message-actions .action-postback.primary:not(:disabled):active svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.primary:not(:disabled):active svg>path,.wrapper .message-bubble-tabular-message .form-actions .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .form-actions .action-postback.primary:not(:disabled):active svg>path,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.primary:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .message-actions .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .message-actions .action-postback.primary:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .table-message-item .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .table-message-item .action-postback.primary:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .form-actions .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .form-actions .action-postback.primary:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .form-message-value .action-postback.primary:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .form-message-value .action-postback.primary:not(:disabled):active svg>path{fill:var(--color-primary-form-actions-text-focus)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.danger,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.danger,.wrapper .message-bubble-tabular-message .form-actions .action-postback.danger,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.danger,.wrapper .message-bubble-form-message .message-actions .action-postback.danger,.wrapper .message-bubble-form-message .table-message-item .action-postback.danger,.wrapper .message-bubble-form-message .form-actions .action-postback.danger,.wrapper .message-bubble-form-message .form-message-value .action-postback.danger{background:var(--color-danger-form-actions-background);color:var(--color-danger-form-actions-text);border:var(--color-danger-form-actions-border)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.danger:not(:disabled):hover,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.danger:not(:disabled):hover,.wrapper .message-bubble-tabular-message .form-actions .action-postback.danger:not(:disabled):hover,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.danger:not(:disabled):hover,.wrapper .message-bubble-form-message .message-actions .action-postback.danger:not(:disabled):hover,.wrapper .message-bubble-form-message .table-message-item .action-postback.danger:not(:disabled):hover,.wrapper .message-bubble-form-message .form-actions .action-postback.danger:not(:disabled):hover,.wrapper .message-bubble-form-message .form-message-value .action-postback.danger:not(:disabled):hover{background:var(--color-danger-form-actions-background-hover);color:var(--color-danger-form-actions-text-hover)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.danger:not(:disabled):hover svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.danger:not(:disabled):hover svg>path,.wrapper .message-bubble-tabular-message .form-actions .action-postback.danger:not(:disabled):hover svg>path,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.danger:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .message-actions .action-postback.danger:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .table-message-item .action-postback.danger:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .form-actions .action-postback.danger:not(:disabled):hover svg>path,.wrapper .message-bubble-form-message .form-message-value .action-postback.danger:not(:disabled):hover svg>path{fill:var(--color-danger-form-actions-text-hover)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-tabular-message .message-actions .action-postback.danger:not(:disabled):active,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.danger:not(:disabled):active,.wrapper .message-bubble-tabular-message .form-actions .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-tabular-message .form-actions .action-postback.danger:not(:disabled):active,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.danger:not(:disabled):active,.wrapper .message-bubble-form-message .message-actions .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-form-message .message-actions .action-postback.danger:not(:disabled):active,.wrapper .message-bubble-form-message .table-message-item .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-form-message .table-message-item .action-postback.danger:not(:disabled):active,.wrapper .message-bubble-form-message .form-actions .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-form-message .form-actions .action-postback.danger:not(:disabled):active,.wrapper .message-bubble-form-message .form-message-value .action-postback.danger:not(:disabled):focus,.wrapper .message-bubble-form-message .form-message-value .action-postback.danger:not(:disabled):active{background:var(--color-danger-form-actions-background-focus);color:var(--color-danger-form-actions-text-focus)}.wrapper .message-bubble-tabular-message .message-actions .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .message-actions .action-postback.danger:not(:disabled):active svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .table-message-item .action-postback.danger:not(:disabled):active svg>path,.wrapper .message-bubble-tabular-message .form-actions .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .form-actions .action-postback.danger:not(:disabled):active svg>path,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-tabular-message .form-message-value .action-postback.danger:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .message-actions .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .message-actions .action-postback.danger:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .table-message-item .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .table-message-item .action-postback.danger:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .form-actions .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .form-actions .action-postback.danger:not(:disabled):active svg>path,.wrapper .message-bubble-form-message .form-message-value .action-postback.danger:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .form-message-value .action-postback.danger:not(:disabled):active svg>path{fill:var(--color-danger-form-actions-text-focus)}.wrapper .message-bubble-form-message{background-color:var(--color-form-background);color:var(--color-form-text)}.wrapper .message-bubble-form-message.edit-form-message{overflow:visible}.wrapper .message-bubble-form-message.edit-form-message .message-actions{border-top:none;padding-top:0}.wrapper .message-bubble-form-message.edit-form-message .form-message-header{border-radius:0 7px 0 0}.wrapper .message-bubble-form-message.edit-form-message .form-message-item{border-radius:0 7px 7px 7px}.wrapper .message-bubble-form-message .results-page-status{background-color:var(--color-form-background);color:var(--color-form-text)}.wrapper .message-bubble-form-message .message-actions .action-postback{background:var(--color-form-actions-background);color:var(--color-form-actions-text);border-color:var(--color-form-actions-border)}.wrapper .message-bubble-form-message .message-actions .action-postback:not(:disabled):hover{color:var(--color-form-actions-text-hover);background:var(--color-form-actions-background-hover)}.wrapper .message-bubble-form-message .message-actions .action-postback:not(:disabled):hover svg>path{fill:var(--color-form-actions-text-hover)}.wrapper .message-bubble-form-message .message-actions .action-postback:not(:disabled):focus,.wrapper .message-bubble-form-message .message-actions .action-postback:not(:disabled):active{background:var(--color-form-actions-background-focus);color:var(--color-form-actions-text-focus)}.wrapper .message-bubble-form-message .message-actions .action-postback:not(:disabled):focus svg>path,.wrapper .message-bubble-form-message .message-actions .action-postback:not(:disabled):active svg>path{fill:var(--color-form-actions-text-focus)}.wrapper .form-message-field,.wrapper .table-message-heading,.wrapper .table-message-item{word-break:normal;overflow-wrap:anywhere}.wrapper .form-message-field:hover .popupContent,.wrapper .table-message-heading:hover .popupContent,.wrapper .table-message-item:hover .popupContent{display:flex}.wrapper .table-message-wrapper{overflow:auto}.wrapper .table-message-wrapper .table-message-table-title-wrapper{background-color:var(--color-table-header-background);border-bottom:1px solid var(--color-table-title-separator);padding:8px}.wrapper .table-message-wrapper .table-message-table-title-wrapper .table-message-table-title{color:var(--color-table-header-text);font-size:14px;font-weight:600;line-height:16px;margin:4px 8px}.wrapper .table-message-wrapper .table-message{min-width:100%;max-width:200%;border-collapse:collapse}.wrapper .table-message-wrapper .table-message .table-message-headings{align-items:center;color:var(--color-table-header-text);background-color:var(--color-table-header-background);display:flex}.wrapper .table-message-wrapper .table-message .table-message-headings .table-message-heading{font-size:12px;font-weight:600;line-height:16px;padding:16px;min-width:120px}.wrapper .table-message-wrapper .table-message .table-message-row{border-top:1px solid var(--color-table-separator);display:flex;align-items:center}.wrapper .table-message-wrapper .table-message .table-message-row .table-message-item{color:var(--color-table-text);font-size:16px;line-height:20px;min-width:120px;padding:10px 16px}.wrapper .table-message-wrapper .table-message .table-message-row .table-message-item .table-message-value.font-size-lg{font-size:18px;line-height:23.5px}.wrapper .table-message-wrapper .table-message .table-message-row .table-message-item .table-message-value.font-size-md{font-size:16px;line-height:21px}.wrapper .table-message-wrapper .table-message .table-message-row .table-message-item .table-message-value.font-size-sm{font-size:13.8px;line-height:18px}.wrapper .table-message-wrapper .table-message .table-message-row .table-message-item .table-message-value.font-weight-bold{font-weight:600}.wrapper .table-message-wrapper .table-message .table-message-row .table-message-item .table-message-value.font-weight-md{font-weight:400}.wrapper .table-message-wrapper .table-message .table-message-row .table-message-item .table-message-value.font-weight-light{font-weight:300}.wrapper .form-message-header{align-items:center;background-color:var(--color-form-header-background);color:var(--color-form-header-text);display:flex;font-weight:700;line-height:20px;padding:16px;text-align:start}.wrapper .form-message-item{color:var(--color-form-text);background-color:var(--color-form-background);display:flex;flex-flow:row wrap;justify-content:space-between;padding:16px}.wrapper .form-message-item .form-row{display:flex;flex:1 0 100%;margin:2px}.wrapper .form-message-item .form-row.separator{border-top:1px solid var(--color-table-separator);margin-top:8px}.wrapper .form-message-item .form-row .form-row-column{display:flex;flex-flow:column wrap;flex:0 1 auto;min-width:0}.wrapper .form-message-item .form-row .form-row-column.stretch{flex-grow:1}.wrapper .form-message-item .form-row .form-row-column.align-center{justify-content:center}.wrapper .form-message-item .form-row .form-row-column.align-start{justify-content:flex-start}.wrapper .form-message-item .form-row .form-row-column.align-end{justify-content:flex-end}.wrapper .form-message-item .form-row .form-row-column:not(:last-child){margin-inline-end:4px}.wrapper .form-message-item .form-row .form-row-column .form-message-field.margin-top-lg{margin-top:28px}.wrapper .form-message-item .form-row .form-row-column .form-message-field.margin-top-md{margin-top:16px}.wrapper .form-message-item .form-row .form-row-column .form-message-field.margin-top-default{margin-top:8px}.wrapper .form-message-item .form-row .form-row-column .edit-form-message-field .listbox{min-width:100%;inset-inline-start:0;max-width:unset}.wrapper .form-message-item.c2k-reference{justify-content:flex-start}.wrapper .form-message-item.c2k-reference .form-row{margin-inline-end:8px;flex-basis:auto;width:auto;line-height:16px;color:rgba(22,21,19,.6509803922)}.wrapper .form-message-item.c2k-reference .form-row .form-row-column:not(:last-child){margin-inline-end:6px}.wrapper .form-message-item.c2k-reference .form-row span.delimiter{margin-inline-end:8px}.wrapper .form-message-item.with-border{border-bottom:1px solid var(--color-table-separator)}.wrapper .form-message-item .form-message-key{color:var(--color-form-label);line-height:16px}.wrapper .form-message-item .form-message-key.font-size-lg{font-size:14px;line-height:18px}.wrapper .form-message-item .form-message-key.font-size-md{font-size:12px;line-height:15.5px}.wrapper .form-message-item .form-message-key.font-size-sm{font-size:10px;line-height:13px}.wrapper .form-message-item .form-message-key.font-weight-bold{font-weight:700}.wrapper .form-message-item .form-message-key.font-weight-md{font-weight:600}.wrapper .form-message-item .form-message-key.font-weight-light{font-weight:400}.wrapper .form-message-item .form-message-key.with-margin{cursor:auto;margin-bottom:8px}.wrapper .form-message-item>.form-message-field:not(:last-child){margin-bottom:16px}.wrapper .form-message-item .form-message-field .form-message-value.font-size-lg{font-size:18px;line-height:23.5px}.wrapper .form-message-item .form-message-field .form-message-value.font-size-md{font-size:16px;line-height:21px}.wrapper .form-message-item .form-message-field .form-message-value.font-size-sm{font-size:13.8px;line-height:18px}.wrapper .form-message-item .form-message-field .form-message-value.font-weight-bold{font-weight:600}.wrapper .form-message-item .form-message-field .form-message-value.font-weight-md{font-weight:400}.wrapper .form-message-item .form-message-field .form-message-value.font-weight-light{font-weight:300}.wrapper .form-message-item .form-message-field .form-message-value.with-top-margin{margin-top:2px}.wrapper .form-message-item .form-message-field .form-message-value button.action-postback{margin-inline-start:0}.wrapper .form-message-item .form-message-field.form-message-field-col-1{flex-basis:100%;max-width:100%}.wrapper .form-message-item .form-message-field.form-message-field-col-2{flex-basis:calc(50% - 12px);max-width:calc(50% - 12px);height:100%}.wrapper .form-message-item .form-message-field.form-message-field-col-2:nth-last-child(2){margin-bottom:0}.wrapper .form-message-item .form-message-field.form-message-field-col-2:nth-child(even) .popupContent{inset-inline-start:calc(50% - 7px)}.wrapper .form-message-item .form-message-field.form-message-field-col-2.edit-form-message-field:nth-child(even) .listbox{inset-inline:auto 16px}.wrapper .form-message-item .form-message-field.form-message-field-col-2.edit-form-message-field .listbox{min-width:calc(50% - 28px)}.wrapper .form-message-item .form-message-field.edit-form-message-field{display:flex;flex-direction:column;overflow:visible;width:100%}.wrapper .form-message-item .form-message-field.edit-form-message-field.disabled{cursor:not-allowed}.wrapper .form-message-item .form-message-field.edit-form-message-field .input.form-message-value,.wrapper .form-message-item .form-message-field.edit-form-message-field .textarea.form-message-value,.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper.form-message-value{border-radius:4px;background-color:var(--color-form-input-background);color:var(--color-form-input-text);border:1px solid var(--color-form-input-border);font-size:16px}.wrapper .form-message-item .form-message-field.edit-form-message-field .input.form-message-value:focus,.wrapper .form-message-item .form-message-field.edit-form-message-field .textarea.form-message-value:focus,.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper.form-message-value:focus{border-color:var(--color-form-input-border-focus);box-shadow:0 0 0 1px var(--color-form-input-border-focus) inset;outline:1px solid rgba(0,0,0,0)}.wrapper .form-message-item .form-message-field.edit-form-message-field .input:disabled,.wrapper .form-message-item .form-message-field.edit-form-message-field .textarea:disabled,.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper:disabled{opacity:.5;cursor:not-allowed}.wrapper .form-message-item .form-message-field.edit-form-message-field .input:disabled~.field-error,.wrapper .form-message-item .form-message-field.edit-form-message-field .textarea:disabled~.field-error,.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper:disabled~.field-error{display:none}.wrapper .form-message-item .form-message-field.edit-form-message-field.error>.input:not(:disabled,.disabled),.wrapper .form-message-item .form-message-field.edit-form-message-field.error>.textarea:not(:disabled,.disabled),.wrapper .form-message-item .form-message-field.edit-form-message-field.error>.select-wrapper:not(:disabled,.disabled),.wrapper .form-message-item .form-message-field.edit-form-message-field.error>.text-field-container:not(:disabled,.disabled){border-color:var(--color-form-error)}.wrapper .form-message-item .form-message-field.edit-form-message-field input.form-message-value{height:42px;padding:0 12px}.wrapper .form-message-item .form-message-field.edit-form-message-field input.form-message-value[type=date]::-webkit-calendar-picker-indicator,.wrapper .form-message-item .form-message-field.edit-form-message-field input.form-message-value[type=time]::-webkit-calendar-picker-indicator,.wrapper .form-message-item .form-message-field.edit-form-message-field input.form-message-value[type=number]::-webkit-inner-spin-button{cursor:pointer;width:20px;height:20px;margin-inline-end:-8px}.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper{align-items:center;display:flex;height:44px}.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper.focus{border-color:var(--color-form-input-border-focus);box-shadow:0 0 0 1px var(--color-form-input-border-focus) inset;outline:1px solid rgba(0,0,0,0)}.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper.disabled{opacity:.5;pointer-events:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper.disabled~.field-error{display:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper .input{width:calc(100% - 36px);border:none;box-shadow:none !important;outline:1px solid rgba(0,0,0,0);height:40px;margin-inline-start:1px}.wrapper .form-message-item .form-message-field.edit-form-message-field .select-wrapper .select-icon{margin-inline-start:0;color:var(--color-form-input-text)}.wrapper .form-message-item .form-message-field.edit-form-message-field textarea.form-message-value{overflow:auto;padding:11px 12px;resize:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .form-container{display:flex;max-width:max-content}.wrapper .form-message-item .form-message-field.edit-form-message-field .form-container.disabled{cursor:not-allowed;opacity:.5}.wrapper .form-message-item .form-message-field.edit-form-message-field .form-container.disabled+.field-error{display:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .form-container .label{display:flex;min-height:36px;align-items:center;padding:7.5px 0;border-bottom:1px solid rgba(0,0,0,0)}.wrapper .form-message-item .form-message-field.edit-form-message-field .form-container .radio-input{margin-inline-end:8px}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container{background-color:var(--color-form-input-background);border-radius:4px;border:1px solid var(--color-form-input-border);display:flex;min-height:44px;flex-direction:row;cursor:text}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container.disabled{opacity:.5;pointer-events:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container.disabled~.field-error{display:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container:focus{border-color:var(--color-form-input-border-focus);box-shadow:0 0 0 1px var(--color-form-input-border-focus) inset;outline:1px solid rgba(0,0,0,0)}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container .selected-options{padding:0 12px 5px}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container .selected-options:empty{padding-top:5px}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container .selected-options:empty:before{content:attr(data-placeholder)}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container .selected-options .multi-select-option{float:left;line-height:16px;display:flex;align-items:center;cursor:default;border-radius:4px;border:1px solid var(--color-form-input-border);color:var(--color-form-input-text);background-clip:padding-box;font-size:12px;margin-inline-end:6px;margin-top:5px;padding-inline:6px 4px}.wrapper .form-message-item .form-message-field.edit-form-message-field .text-field-container .selected-options .multi-select-option .opt-close{cursor:pointer;height:16px;width:16px}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox{border:1px solid var(--color-table-separator);border-radius:4px;display:flex;flex-direction:column;margin-top:3px;inset-inline-start:16px;max-width:calc(100% - 32px);min-width:calc(100% - 32px);z-index:3}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .filter-message-box{display:flex;flex-direction:column;padding:0 12px}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .filter-message-box .filter-message-text{color:var(--color-form-label);font-size:13.75px;height:42px;padding:12px 0;border-bottom:1px solid var(--color-table-separator)}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .listbox-search{flex-shrink:0;margin:12px;padding-inline-end:36px}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .search-icon-wrapper{position:relative;height:0}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .search-icon-wrapper .search-icon{position:absolute;inset-inline-end:21px;bottom:23px}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .multi-select-list,.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .single-select-list{animation:none;display:block;max-height:400px;margin:1px 0 2px 0;overflow-y:auto;padding:8px 0;z-index:3}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .multi-select-list .li,.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .single-select-list .li{height:auto;margin:0;padding:12px}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .multi-select-list .li:not(.none).selected,.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .single-select-list .li:not(.none).selected{border-top:1px solid #227e9e;background-color:#e4f1f7}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .multi-select-list .li:not(.none).selected:last-child,.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .single-select-list .li:not(.none).selected:last-child{box-shadow:inset 0 -1px 0 0 #227e9e}.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .multi-select-list .li:not(.none).selected+li,.wrapper .form-message-item .form-message-field.edit-form-message-field .listbox .single-select-list .li:not(.none).selected+li{border-top:1px solid #227e9e}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle{position:relative;width:36px;height:20px}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle.disabled+.field-error{display:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle .input{display:none}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle .input:disabled+.round-slider{cursor:not-allowed;opacity:.5}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle .input:checked+.round-slider{background-color:#227e9e;border-color:#227e9e}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle .input:checked+.round-slider:before{inset-inline:auto 1px;transition:height .3s cubic-bezier(0, 0, 0.2, 1),width .3s cubic-bezier(0, 0, 0.2, 1),right .3s cubic-bezier(0, 0, 0.2, 1)}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle .round-slider{position:absolute;cursor:pointer;background-color:#8b8580;transition:background-color .2s linear .1s,opacity .2s linear .1s,border-color .2s linear .1s;border:1px solid rgba(0,0,0,0);border-radius:4px;height:20px;width:36px}.wrapper .form-message-item .form-message-field.edit-form-message-field .toggle .round-slider:before{border-radius:4px;width:16px;height:16px;inset-inline:1px auto;position:absolute;content:"";bottom:1px;background-color:var(--color-form-background);transition:height .3s cubic-bezier(0, 0, 0.2, 1),width .3s cubic-bezier(0, 0, 0.2, 1),left .3s cubic-bezier(0, 0, 0.2, 1)}.wrapper .form-message-item span.field-error{display:flex;margin-top:2px;line-height:16px}.wrapper .form-message-item span.field-error .error-text{color:var(--color-form-error-text);font-size:12px;margin-inline-start:4px}.wrapper .form-message-item span.field-error svg.form-error-icon{position:relative;height:16px;width:16px;fill:var(--color-form-error);flex-shrink:0}.wrapper .form-message-item span.field-error.form-error{padding:8px;background:var(--color-error-message-background);border-radius:4px;margin:10px 0;border:thin dashed var(--color-error-border);width:100%}.wrapper .form-message-item span.field-error.form-error.disabled{display:none}.wrapper .form-message-item span.field-error.form-error svg.form-error-icon{top:0}.wrapper .form-message-item span.field-error.form-error .error-text{font-weight:600;color:var(--color-error-title);margin-inline-start:8px;font-size:14px}.wrapper .form-message-item span.field-required-tip-end,.wrapper .form-message-item span.field-required-tip{display:flex;flex-direction:column;margin-top:2px;line-height:16px}.wrapper .form-message-item span.field-required-tip-end .required-tip-text,.wrapper .form-message-item span.field-required-tip .required-tip-text{color:var(--color-form-required-tip);font-size:12px;margin-inline-start:4px;margin-inline-end:4px}.wrapper .form-message-item span.field-required-tip-end{align-items:end}.wrapper .form-message-item .form-actions .action-postback,.wrapper .form-message-item .form-message-value .action-postback{background:var(--color-form-actions-background);color:var(--color-form-actions-text);border-color:var(--color-form-actions-border)}.wrapper .form-message-item .form-actions .action-postback:not(:disabled):hover,.wrapper .form-message-item .form-message-value .action-postback:not(:disabled):hover{color:var(--color-form-actions-text-hover);background:var(--color-form-actions-background-hover)}.wrapper .form-message-item .form-actions .action-postback:not(:disabled):hover svg>path,.wrapper .form-message-item .form-message-value .action-postback:not(:disabled):hover svg>path{fill:var(--color-form-actions-text-hover)}.wrapper .form-message-item .form-actions .action-postback:not(:disabled):focus,.wrapper .form-message-item .form-actions .action-postback:not(:disabled):active,.wrapper .form-message-item .form-message-value .action-postback:not(:disabled):focus,.wrapper .form-message-item .form-message-value .action-postback:not(:disabled):active{background:var(--color-form-actions-background-focus);color:var(--color-form-actions-text-focus)}.wrapper .form-message-item .form-actions .action-postback:not(:disabled):focus svg>path,.wrapper .form-message-item .form-actions .action-postback:not(:disabled):active svg>path,.wrapper .form-message-item .form-message-value .action-postback:not(:disabled):focus svg>path,.wrapper .form-message-item .form-message-value .action-postback:not(:disabled):active svg>path{fill:var(--color-form-actions-text-focus)}.wrapper .tableform-message .table-message-row{cursor:pointer}.wrapper .tableform-message .table-message-row:hover{background-color:var(--color-table-row-background-hover)}.wrapper .tableform-message .table-message-row .widget-button:hover,.wrapper .tableform-message .table-message-row .widget-button:active,.wrapper .tableform-message .table-message-row .widget-button:focus{background-color:unset}.wrapper .tableform-message .table-message-headings .table-message-heading:last-child,.wrapper .tableform-message .table-message-row .table-message-item:last-child{min-width:unset;padding:0}.wrapper .tableform-message .table-message-headings .table-message-heading:last-child .widget-button,.wrapper .tableform-message .table-message-row .table-message-item:last-child .widget-button{margin:0 2px;transition:transform .25s ease-in-out}.wrapper .tableform-message .table-message-headings .table-message-heading:last-child .widget-button.rotate-180,.wrapper .tableform-message .table-message-row .table-message-item:last-child .widget-button.rotate-180{transform:rotate3d(0, 0, 1, 180deg)}.wrapper .tableform-message .form-message-item{margin:0;padding:16px;transition:all .25s ease-in-out;border-bottom:none}.wrapper .tableform-message .form-message-item:last-child{border-top:1px solid var(--color-table-bottom)}.wrapper .footer-form{width:100%}.wrapper .footer-form .message-bubble-form-message{background:rgba(0,0,0,0);border:none;width:100%}.wrapper .footer-form .message-bubble-form-message .form-message-item{background:rgba(0,0,0,0);padding:0}.wrapper .footer-form .message-bubble-form-message .form-message-item .form-message-key{color:var(--color-footer-form-label)}.wrapper.embedded .open{width:100%;height:100%}.wrapper.embedded .open .widget{border-radius:0;width:100%;min-width:100%;max-width:100%;height:100%;position:inherit;box-shadow:none;max-height:unset}.wrapper.popup-content-wrapper{background:rgba(22,21,19,.4);width:100vw;height:100vh;position:fixed;z-index:10000;top:0 !important;left:0 !important;display:flex;align-items:center;justify-content:center}.wrapper.popup-content-wrapper .popup-dialog{overflow:hidden;max-width:600px;border-radius:6px;box-shadow:0px 6px 12px 0px rgba(0,0,0,.2);max-height:calc(100vh - 16px)}.wrapper.popup-content-wrapper .popup-dialog .popup-header{justify-content:flex-end;background-color:#fff;height:56px;padding:0 8px}.wrapper.popup-content-wrapper .popup-dialog .message-bubble{width:auto;padding:32px;margin-top:0;border-radius:0;overflow:auto;max-height:calc(100vh - 16px)}.wrapper.popup-content-wrapper .popup-dialog .message-bubble:last-child{border-radius:0}.wrapper.popup-content-wrapper .popup-dialog .message-bubble.message-header{display:none}.wrapper.popup-content-wrapper .popup-dialog .message-bubble.message-bubble-form-message{padding:0}.wrapper.popup-content-wrapper .popup-dialog .message-bubble.message-bubble-form-message:last-child .form-message-header{border-radius:0}.wrapper.popup-content-wrapper .popup-dialog .message-bubble.message-bubble-form-message:last-child .form-message-item{border-radius:0}.wrapper.popup-content-wrapper .popup-dialog .message-bubble.message-bubble-form-message .form-message-header{padding:32px 32px 12px;border-radius:0;justify-content:space-between}.wrapper.popup-content-wrapper .popup-dialog .message-bubble.message-bubble-form-message .form-message-item{padding:0 32px 32px;border-radius:0}.wrapper .full-screen-modal{position:fixed;top:0;left:0;width:100%;height:100vh;z-index:1000000;background-color:rgba(0,0,0,.8)}.wrapper .modal-header{background:linear-gradient(180deg, rgba(0, 0, 0, 0.5), transparent);color:#fff;display:flex;justify-content:space-between;position:relative;padding:10px 20px;z-index:1000001}.wrapper .modal-header .close-btn{border:none;background:rgba(0,0,0,0);cursor:pointer}.wrapper .full-screen-image{position:absolute;max-width:100vw;max-height:100vh;margin:auto;top:0;bottom:0;left:0;right:0}.wrapper .typing-cue-wrapper{width:32px;margin:auto;display:flex}.wrapper .typing-cue-wrapper .typing-cue{position:relative;left:0;right:0;margin:auto;width:8px;height:8px;border-radius:50%;background-color:var(--color-typing-indicator);animation:typing-cue 1550ms infinite linear alternate;animation-delay:250ms;opacity:.1}.wrapper .typing-cue-wrapper .typing-cue::before,.wrapper .typing-cue-wrapper .typing-cue::after{content:"";display:inline-block;position:absolute;width:8px;height:8px;border-radius:50%;background-color:var(--color-typing-indicator);animation:typing-cue 1550ms infinite linear alternate;opacity:.1}.wrapper .typing-cue-wrapper .typing-cue::before{left:-12px;animation-delay:0s}.wrapper .typing-cue-wrapper .typing-cue::after{left:12px;animation-delay:500ms}.wrapper .hidden{border:0;clip:rect(0 0 0 0);height:1px;margin:-1px;overflow:hidden;padding:0;position:absolute;width:1px}.wrapper .rating-root{display:flex}.wrapper [dir=rtl] .rating-root{flex-direction:row-reverse}.wrapper .rating-wrapper{display:flex;margin-top:8px}.wrapper [dir=rtl] .rating-wrapper{flex-direction:row-reverse}.wrapper .rating-hidden{border:0;clip:rect(0 0 0 0);height:1px;margin:-1px;overflow:hidden;padding:0;position:absolute;width:1px}.wrapper .star-label{background-color:rgba(0,0,0,0);border:0;cursor:pointer;padding:0}.wrapper .star-label>svg>path{fill:var(--color-rating-star)}.wrapper .star-input.active+label>svg>path{fill:var(--color-rating-star-fill)}.wrapper .star-input:disabled+.star-label{cursor:not-allowed;filter:brightness(0.8)}.wrapper .rating-star-icon{height:32px;width:32px}.wrapper.expanded .widget:not(.drag){animation:scale-in-br .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}.wrapper.expanded .widget.sidepanel{animation:unset}.wrapper.expanded .widget .resizable{width:4px;height:100%;top:0;left:0;background-color:rgba(0,0,0,0);position:absolute;z-index:10000;cursor:col-resize}.wrapper.expanded .widget .resizable.right-resize{right:0;left:unset}.wrapper.expanded .widget .resizable.top-resize{width:100%;height:4px;cursor:row-resize}.wrapper.expanded .widget .resizable.corner{height:8px;width:8px;cursor:nwse-resize}.wrapper.expanded .widget .resizable.corner.right-resize{cursor:nesw-resize}.wrapper.expanded:not(.pos-left) .right-resize{display:none}.wrapper.expanded .button:not(.drag){animation:scale-out-center .25s cubic-bezier(0.55, 0.085, 0.68, 0.53) forwards}.wrapper.collapsed .widget:not(.drag){animation:scale-out-br .25s cubic-bezier(0.55, 0.085, 0.68, 0.53) forwards}.wrapper.collapsed .widget.sidepanel{animation:unset}.wrapper.collapsed .notification-badge{background-color:var(--color-notification-badge-background);color:var(--color-notification-badge-text);right:-5px;top:-5px;align-items:center;border-radius:24px;display:flex;font-size:14px;height:24px;justify-content:center;position:absolute;text-align:center;width:32px}.wrapper.collapsed .button:not(.drag){animation:scale-in-center .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}.wrapper.pos-left .widget{right:unset;left:calc(var(--position-left)*-1);max-width:100vw}.wrapper.pos-left.expanded .widget:not(.drag){animation:scale-in-bl .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}.wrapper.pos-left.expanded .widget .left-resize{display:none}.wrapper.pos-left.collapsed .widget{animation:scale-out-bl .25s cubic-bezier(0.55, 0.085, 0.68, 0.53) forwards}.wrapper .ellipsis{display:inline-block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:100%}.wrapper .popup{position:absolute;background-color:var(--color-popup-background);color:var(--color-popup-text);min-width:140px;max-height:280px;display:none;padding:4px 0;border-radius:6px;box-shadow:rgba(0,0,0,.16) 0px 4px 8px 0px;overflow-y:auto;z-index:5}.wrapper .popup .li{display:flex;align-items:center;height:48px;margin:4px 0;cursor:pointer;overflow:hidden;color:var(--color-popup-button-text)}.wrapper .popup .li svg>path{fill:var(--color-popup-text)}.wrapper .popup .li#action-menu-option-lang{border-top:1px solid var(--color-popup-horizontal-rule)}.wrapper .popup .li.disable{pointer-events:none;cursor:not-allowed;opacity:.5}.wrapper .popup .li:focus{outline:1px dotted var(--color-actions-outline-focus);outline-offset:1px}.wrapper .popup .li:hover,.wrapper .popup .li:focus,.wrapper .popup .li.active{background-color:var(--color-popup-item-background-hover)}.wrapper .popup .li .icon{margin-inline-start:16px;height:20px;width:20px}.wrapper .popup .li .text{padding:0 16px 0 16px}.wrapper .popup.expand{display:block;-webkit-animation:scale-in-br .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both;animation:scale-in-br .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}.wrapper .popup.action-menu,.wrapper .popup.language-selection-menu{top:50px;bottom:unset}.wrapper .popup.action-menu.expand,.wrapper .popup.language-selection-menu.expand{display:block;-webkit-animation:scale-in-tr .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both;animation:scale-in-tr .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}.wrapper .popup.language-selection-menu{max-height:calc(100% - 280px)}.wrapper .popup.share-popup-list{bottom:50px;left:unset}.wrapper .spinner{height:48px;width:48px}.wrapper .spinner svg{animation-duration:750ms;-webkit-animation:spin 1s linear infinite;animation:spin 1s linear infinite}.wrapper .spinner svg circle{fill:rgba(0,0,0,0);stroke:var(--color-user-text);stroke-width:2px;stroke-dasharray:128px;stroke-dashoffset:82px}.wrapper .webview-container{position:absolute;width:100%;height:80%;bottom:0;box-shadow:0px -4px 32px rgba(0,0,0,.1);z-index:10}.wrapper .webview-container .webview-header svg{fill:var(--color-actions-text)}.wrapper .webview-container .webview-header .widget-button{color:var(--color-actions-text)}.wrapper .webview-container .spinner{position:absolute;margin:auto;left:0;right:0;top:40%}.wrapper .webview-container .iframe{width:100%;height:100%;background:var(--color-conversation-background);border:none}.wrapper .webview-container .webview-error{position:absolute;bottom:0;background:var(--color-popup-background);width:calc(100% - 32px);margin:10px 16px;padding:6px 16px;border-radius:6px;display:flex;align-items:center;box-shadow:0px -4px 32px rgba(0,0,0,.1)}.wrapper .webview-container .webview-error .webview-error-button-close{border:none}.wrapper .webview-container .webview-alt-link{color:var(--color-links)}.wrapper .webview-container.webview-container-close{animation:webview-slide-out-bottom .4s cubic-bezier(0.55, 0.085, 0.68, 0.53) both}.wrapper .webview-container.webview-container-open{animation:webview-slide-in-bottom .4s cubic-bezier(0.25, 0.46, 0.45, 0.94) both}.wrapper .pin-button-wrapper{position:sticky;display:flex;justify-content:end;top:0px;z-index:2}.wrapper .pin-button-wrapper .widget-button{border:0px;background-color:#fff}.wrapper .pin-button-wrapper .widget-button:hover{background-color:#e9e7e7}.wrapper .pin-button-wrapper .widget-button:active{background-color:#d7d5d3}.wrapper .scroll-down-button-wrapper{position:sticky;display:flex;justify-content:center;bottom:-8px;padding-bottom:16px;background:linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, #FFFFFF 100%)}.wrapper .scroll-down-button-wrapper .widget-button{border-radius:35px;background-color:#fff;box-shadow:0px 6px 12px 0px rgba(0,0,0,.2)}.wrapper .scroll-down-button-wrapper .widget-button:hover{background-color:#e9e7e7}.wrapper .scroll-down-button-wrapper .widget-button:active{background-color:#d7d5d3}.widget{position:absolute;bottom:calc(var(--position-bottom)*-1);border-radius:6px 6px 0 0;box-shadow:0px -4px 32px rgba(0,0,0,.1);right:calc(var(--position-right)*-1);width:100vw;min-width:100vw;max-width:100vw;max-height:var(--widget-max-height);margin:0;overflow:hidden;text-decoration:none;text-transform:none;z-index:10000;align-items:stretch;background:var(--color-conversation-background)}.widget.large-size{--bubble-max-width: 780px}.wrapper .widget.large-size{font-size:18px;line-height:24px}.wrapper .widget.large-size .card{padding:24px}.wrapper .widget.large-size .card .card-content{margin-bottom:24px}.wrapper .widget.large-size .card .card-image{margin:-24px -24px 10px;width:calc(100% + 48px)}.wrapper .widget.large-size .message-bubble{line-height:24px;padding:16px 24px}.wrapper .widget.large-size .attachment .attachment-placeholder{margin:-16px -24px 0;max-width:calc(100% + 48px)}.wrapper .widget.large-size .attachment .attachment-footer{margin:0 -24px -16px}.wrapper .widget.large-size .widget-button:not(.icon){height:44px}.wrapper .widget.large-size .footer{border-radius:20px 20px 0 0;margin:0 24px;overflow:hidden}.wrapper .widget.large-size .footer.left{margin-inline-start:68px}.wrapper .widget.large-size .footer.right{margin-inline-end:68px}.wrapper .widget.large-size .footer-actions{margin-inline-end:10px}.wrapper .widget.large-size .user-input{font-size:18px;line-height:24px;min-height:60px;padding:18px 12px 18px 18px}.wrapper .widget.medium-size{font-size:16px;line-height:20px}.wrapper .widget.medium-size .card{padding:16px}.wrapper .widget.medium-size .card .card-content{margin-bottom:16px}.wrapper .widget.medium-size .card .card-image{margin-top:-16px}.wrapper .widget.medium-size .message-bubble{line-height:20px;padding:8px 16px}.wrapper .widget.medium-size .attachment .attachment-placeholder{margin:-8px -16px 0}.wrapper .widget.medium-size .attachment .attachment-footer{margin:0 -16px -8px}.wrapper .widget.medium-size .footer{border-radius:20px 20px 0 0;margin:0 24px;overflow:hidden}.wrapper .widget.medium-size .user-input{font-size:16px;line-height:20px;min-height:60px;padding:20px 12px 20px 10px}.wrapper .widget.large-size .icon-wrapper,.wrapper .widget.medium-size .icon-wrapper{height:36px;width:36px;min-height:36px;min-width:36px}.wrapper .widget.large-size .message.card-message-horizontal,.wrapper .widget.medium-size .message.card-message-horizontal{margin-inline-start:-24px}.wrapper .widget.large-size .message.card-message-horizontal .message-header,.wrapper .widget.large-size .message.card-message-horizontal .message-footer,.wrapper .widget.large-size .message.card-message-horizontal .message-global-actions,.wrapper .widget.medium-size .message.card-message-horizontal .message-header,.wrapper .widget.medium-size .message.card-message-horizontal .message-footer,.wrapper .widget.medium-size .message.card-message-horizontal .message-global-actions{margin-inline-start:24px;max-width:calc(.9*(100% - 36px))}.wrapper .widget.large-size .message.card-message-horizontal .card-message-cards,.wrapper .widget.medium-size .message.card-message-horizontal .card-message-cards{padding-inline-start:24px}.wrapper .widget.large-size .card,.wrapper .widget.medium-size .card{width:344px}.wrapper .widget.large-size .conversation,.wrapper .widget.medium-size .conversation{padding:16px 24px}.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal{margin-inline-start:-68px}.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-header,.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-footer,.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-global-actions,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-header,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-footer,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .message-global-actions{margin-inline-start:68px}.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .card-message-content .card-message-cards,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message.card-message-horizontal .card-message-content .card-message-cards{padding-inline-start:68px}.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .relative-timestamp.left,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .relative-timestamp.left{margin-inline-start:44px}.wrapper .widget.large-size .conversation .conversation-pane.user-icon .relative-timestamp.right,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon .relative-timestamp.right{margin-inline-end:44px}.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper,.wrapper .widget.large-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper{max-width:min(var(--bubble-max-width),.9*(100% - 44px))}.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .widget.large-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions,.wrapper .widget.large-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .widget.large-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .widget.large-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .widget.medium-size .conversation .conversation-pane.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions{max-width:min(var(--bubble-max-width),.9*(100% - 92px))}.wrapper .widget.large-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper{max-width:min(var(--bubble-max-width),.9*(100% - 88px))}.wrapper .widget.large-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .widget.large-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .widget.large-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-header,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-footer,.wrapper .widget.medium-size .conversation .conversation-pane.user-icon.bot-icon .message-block .messages-wrapper .message.card-message-horizontal .message-global-actions{max-width:min(var(--bubble-max-width),.9*(100% - 136px))}.wrapper .widget.large-size .message-bubble-tabular-message,.wrapper .widget.large-size .message-bubble-form-message,.wrapper .widget.medium-size .message-bubble-tabular-message,.wrapper .widget.medium-size .message-bubble-form-message{padding:0}.widget .alert-wrapper{position:absolute;top:48px;width:100%}.widget .alert-wrapper .alert-prompt{position:relative;left:0;right:0;width:auto;margin:6px;padding:10px;border-radius:10px;z-index:11}.widget .msg-icon{padding:5px 10px 0 0}.widget .msg{flex-grow:1}.sidepanel-content-wrapper{display:flex;width:100vw}.sidepanel-content-wrapper>*{flex-grow:1}.sidepanel-content-wrapper .wrapper:not(.contextual-widget){position:absolute;bottom:0;right:0;height:100vh;flex-grow:unset;width:0;min-width:0;max-width:0;flex-shrink:0;--width-full-screen: 375px}.sidepanel-content-wrapper .wrapper:not(.contextual-widget).expanded{min-width:100vw;max-width:100vw}.sidepanel-content-wrapper .wrapper:not(.contextual-widget).expanded::after{content:"";background-color:rgba(0,0,0,0);position:absolute;top:0;left:0;width:4px;height:100%;cursor:col-resize;z-index:10000}.sidepanel-content-wrapper .wrapper:not(.contextual-widget).expanded.drag{transition:unset}.sidepanel-content-wrapper .wrapper:not(.contextual-widget).expanded.drag::after{background-color:#ccc}.sidepanel-content-wrapper .widget{position:relative;bottom:0;right:0;left:0;top:0;width:100%;min-width:unset;max-width:unset;height:100%;max-height:100%;box-shadow:none;border-radius:0}.contextual-widget-wrapper{position:relative}.contextual-widget-wrapper .widget-wrapper{position:sticky;height:0;z-index:1;top:8px;max-width:100%}.contextual-widget-wrapper .widget-wrapper .container{position:absolute;right:-44px}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget{position:relative;width:272px;border-radius:6px;background-color:#f5f4f2;box-shadow:0px 6px 12px 0px rgba(0,0,0,.2)}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.minimum-size{width:36px;box-shadow:0px 1px 4px 0px rgba(0,0,0,.1215686275);border-radius:4px}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.minimum-size.no-feedback>:first-child{border-bottom:none}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.minimum-size.no-feedback>:not(:first-child){display:none}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.minimum-size>:not(:last-child){border-bottom:1px solid rgba(22,21,19,.1215686275)}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.minimum-size .widget-button{background:#f5f4f2;margin-inline-start:0;border-radius:0}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.full-size{width:416px;display:block}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.full-size .conversation .message-wrapper{border-bottom:1px solid rgba(22,21,19,.1215686275)}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget.full-size .footer.enabled{display:block}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget:not(.full-size) .message-actions>:only-child,.contextual-widget-wrapper .widget-wrapper .container .contextual-widget:not(.full-size) .message-actions>:nth-child(2){border:none}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .header{height:44px;background:#f5f4f2;padding:8px 12px 0}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .header .logo{height:16px;width:16px}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .header .title{height:16px;font-weight:400;font-size:12px;line-height:16px;color:rgba(22,21,19,.6980392157)}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .error-message{display:flex;height:76px;border-radius:6px;border:1px solid rgba(22,21,19,.1215686275);margin:0 12px 12px;background:#fef9f2;padding:8px}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .error-message .error-icon{height:18px;margin:8px;padding-top:2px;width:16px}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .error-message .error-info{margin:8px 0}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .error-message .error-info .error-text{color:#8f520a;line-height:20px;font-weight:700}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .error-message .error-info .reset-button{cursor:pointer;line-height:16px;font-size:13.75px;font-weight:600;margin-top:8px;color:#161513}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .message-global-actions{margin-top:0px;padding:12px 12px 4px;background:#fff}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .message-global-actions button.action-postback{height:auto}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .message-wrapper{padding:0 12px 0}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .message-wrapper .message-actions{margin-top:0;margin-bottom:4px;padding:0}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .message-wrapper .message-actions .action-postback{background:rgba(0,0,0,0)}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .message-bubble{font-size:13.75px;line-height:16px;margin-top:0;margin-bottom:0;background:rgba(0,0,0,0);border-radius:0;min-height:unset;padding:0 !important}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .message-bubble .message-text{margin-bottom:12px}.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .footer,.contextual-widget-wrapper .widget-wrapper .container .contextual-widget .footer-form{display:none}.contextual-widget-wrapper .widget-wrapper .container .generate-spinner{background-color:#f5f4f2;box-sizing:border-box;width:154px;height:52px;padding:8px 12px;border-radius:6px;box-shadow:0px 6px 12px 0px rgba(0,0,0,.2);position:sticky;top:8px;bottom:8px;z-index:1;display:flex;align-items:center}.contextual-widget-wrapper .widget-wrapper .container .generate-spinner .generate-icon{height:16px;width:16px}.contextual-widget-wrapper .widget-wrapper .container .generate-spinner .generate-icon.spin{-webkit-animation:spin 1s linear infinite;animation:spin 1s linear infinite}.contextual-widget-wrapper .widget-wrapper .container .generate-spinner .generate-text{width:70px;height:16px;font-size:12px;line-height:16px;color:rgba(22,21,19,.6980392157)}.contextual-widget-wrapper .widget-wrapper .container .generate-spinner .close-button{border:rgba(0,0,0,0);cursor:pointer;background:#f5f4f2;width:36px;height:36px;padding:8px}.contextual-widget-wrapper .widget-wrapper .container .generate-spinner>:not(:last-child){margin-inline-end:4px}.contextual-widget-wrapper .widget-wrapper .widget{position:relative;bottom:0;right:0;left:0;top:0;width:100%;height:100%;border-radius:6px}.search-bar-widget-wrapper{display:flex;gap:8px;height:100%;min-height:44px;position:relative}.search-bar-widget-wrapper .dialog-wrapper{position:relative}.search-bar-widget-wrapper .dialog-wrapper .dialog{position:relative}.search-bar-widget-wrapper .footer{border:none;box-shadow:none;background:rgba(0,0,0,0);height:100%;width:100%;display:flex}.search-bar-widget-wrapper .footer.mode-voice+.search-bar-widget .search-bar-popup{display:none}.search-bar-widget-wrapper .footer .footer-mode-keyboard{display:flex;align-items:flex-start;min-height:unset;margin:0;border:0;background:rgba(0,0,0,0);height:100%;top:0;position:relative;width:100%}.search-bar-widget-wrapper .footer .footer-mode-voice{position:absolute;left:0;right:0;top:calc(100% + 2px);border:1px solid rgba(22,21,19,.12);border-radius:0px 0px 6.06px 6.06px}.search-bar-widget-wrapper .footer .user-input{height:100%;min-height:unset;padding:4px;line-height:unset}.search-bar-widget-wrapper .footer .footer-actions{height:100%}.search-bar-widget-wrapper .footer .footer-actions .share-popup-list{max-height:unset;bottom:unset;animation:none}.search-bar-widget-wrapper .autocomplete-items{max-height:unset;top:56px;bottom:unset}.search-bar-widget-wrapper .search-bar-widget{position:absolute;bottom:0;height:0;width:100%}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content{position:relative;top:4px;background:#fff;min-width:100%;width:100%;max-width:100%;border-radius:6.06px;border:1px solid rgba(22,21,19,.12);padding:8px;box-shadow:0 12px 20px rgba(0,0,0,0.2784313725);max-height:40vh;overflow:hidden auto;scroll-behavior:smooth;scrollbar-width:thin;transition:all .2s ease-in-out}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup{position:relative;display:flex;flex-direction:column;--color-conversation-background: #fff}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup:empty{display:none !important}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .user-message{font-weight:bold;font-size:large;margin-bottom:8}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .user-message:first-child{padding-inline-end:24px}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .user-message:not(:first-child){margin-top:16px}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .message{max-width:100%}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .message.card-message-horizontal{margin-inline:0;width:100vw}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .message-bubble.error{background:var(--color-bot-message-background);border:none;color:var(--color-bot-text)}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .message-bubble-tabular-message,.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .message-bubble-form-message{width:unset;max-width:100%;margin-inline:16px;border-radius:0}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .message-global-actions{margin-top:0px;padding-inline:16px;padding-bottom:8px}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup .attachment-placeholder{padding-inline-start:16px;background-color:#fff}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .search-bar-popup-pinned{margin-top:-32px}.search-bar-widget-wrapper .search-bar-widget .search-bar-widget-content .input-popup-slot{position:relative}.search-bar-widget-wrapper .search-bar-popup-separator{border:1px solid var(--color-search-bar-separator);height:0;margin:8px 0}.search-bar-widget-wrapper .input-start-slot,.search-bar-widget-wrapper .input-end-slot,.search-bar-widget-wrapper .input-popup-slot{word-break:normal;overflow-wrap:anywhere}.search-bar-widget-wrapper .input-end-slot{flex:1 1 auto;overflow-x:auto}.search-bar-widget-pinned-wrapper{position:relative;width:100%;background:#fff;padding:8px;overflow:hidden auto;scroll-behavior:smooth;scrollbar-width:thin;z-index:0}.search-bar-widget-pinned-wrapper .search-bar-popup-pinned{margin-top:-32px}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content:empty{display:none !important}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .user-message{font-weight:bold;font-size:large;margin-bottom:8}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .user-message:first-child{padding-inline-end:24px}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .user-message:not(:first-child){margin-top:16px}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .message{max-width:100%}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .message.card-message-horizontal{margin-inline:0;width:100vw}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .message-bubble.error{background:var(--color-bot-message-background);border:none;color:var(--color-bot-text)}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .message-bubble-tabular-message,.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .message-bubble-form-message{width:unset;max-width:100%;margin-inline:16px;border-radius:0}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .message-global-actions{margin-top:0px;padding-inline:16px;padding-bottom:8px}.search-bar-widget-pinned-wrapper .search-bar-widget-pinned-content .attachment-placeholder{padding-inline-start:16px;background-color:#fff}.image-preview-wrapper{background:rgba(0,0,0,.8);height:100%;position:fixed;top:0;left:0;width:100%;z-index:10000}.image-preview-wrapper .image-preview-header{align-items:center;background:linear-gradient(180deg, rgba(0, 0, 0, 0.5), transparent);color:#fff;display:flex;justify-content:space-between;position:relative;padding:10px 20px;z-index:1000001}.image-preview-wrapper .image-preview-header .image-preview-close{background:rgba(0,0,0,0);border:none;cursor:pointer;height:36px;width:36px}.image-preview-wrapper .image-preview-header .image-preview-close .image-preview-close-icon{fill:#fff;height:100%;width:100%}.image-preview-wrapper .image-preview{bottom:0;left:0;margin:auto;max-height:100vh;max-width:100vw;position:absolute;right:0;top:0}.arrow-icon{margin-inline-end:2px;width:32px;height:32px;display:flex;align-items:center;flex-shrink:0}@media screen and (min-width: 426px){.wrapper.pos-left .widget{left:0}.wrapper:not(.embedded) .widget:not(.sidepanel){max-width:calc(100vw - var(--position-right))}.wrapper:not(.embedded).pos-left .widget:not(.sidepanel){max-width:calc(100vw - var(--position-left))}.widget:not(.sidepanel){width:var(--width-full-screen);min-width:unset;max-height:var(--widget-max-height);bottom:0;right:0}.user-input{font-size:13.75px}.sidepanel-content-wrapper .wrapper.wrapper:not(.contextual-widget){position:sticky;top:0}.sidepanel-content-wrapper .wrapper.wrapper:not(.contextual-widget).expanded{min-width:375px;max-width:800px}.sidepanel-content-wrapper .wrapper.wrapper:not(.contextual-widget) .widget{border-left:thin solid #ccc}}@media(prefers-reduced-motion){.open{animation:none}.close{animation:none}}[dir=rtl] .wrapper *{direction:rtl}[dir=rtl] .multi-select-option{float:right !important}[dir=rtl] .wrapper{text-align:right}[dir=rtl] .wrapper .widget.open{animation:scale-in-bl .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}[dir=rtl] .wrapper .widget.close{animation:scale-out-bl .25s cubic-bezier(0.55, 0.085, 0.68, 0.53) forwards}[dir=rtl] .wrapper .message-bubble{border-radius:10px 2px 2px 10px}[dir=rtl] .wrapper .message-block .message:last-child .message-bubble:last-child{border-radius:10px 2px 10px 10px}[dir=rtl] .wrapper .message-block.right .messages-wrapper .message .message-bubble{border-radius:2px 10px 10px 2px}[dir=rtl] .wrapper .message-block.right .messages-wrapper .message:last-child .message-bubble:last-child{border-radius:2px 10px 10px 10px}[dir=rtl] .wrapper .button{left:0;right:unset}[dir=rtl] .wrapper .popup.expand{-webkit-animation:scale-in-bl .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both;animation:scale-in-bl .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}[dir=rtl] .wrapper .popup.action-menu.expand,[dir=rtl] .wrapper .popup.language-selection-menu.expand{-webkit-animation:scale-in-tl .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both;animation:scale-in-tl .25s cubic-bezier(0.25, 0.46, 0.45, 0.94) .2s both}'.replace(
                /(\.)([a-zA-Z_-]+)(?=[^}]+{)/gi,
                `$1${this.Xi}-$2`
              )
            )
          );
          for (let i = 0; i < t.length; i++) {
            const o = t.item(i);
            if ("style" === o.nodeName.toLowerCase()) {
              document.head.insertBefore(s, o), (e = !0);
              break;
            }
          }
          e || document.head.appendChild(s), (this.styleSheet = s);
        }
        !(function (e, t) {
          if (e) {
            const s = ["headerBackground", "visualizer", "ratingStarFill"],
              i = ["botText", "userText"],
              o = Object.assign({}, e);
            s.forEach((t) => {
              o[t] = e[t] || e.branding;
            }),
              i.forEach((t) => {
                o[t] = e[t] || e.text;
              }),
              Object.keys(o).forEach((e) => {
                const s = o[e];
                if (s)
                  if ("shareMenuText" === e)
                    t.updateCSSVar("--color-popup-button-text", s);
                  else {
                    const i = `--color-${e
                      .replace(/([A-Z&])/g, "-$1")
                      .toLowerCase()}`;
                    t.updateCSSVar(i, s);
                  }
              });
          }
        })(e.colors, this.fs);
      }
      Wh() {
        var e;
        const t = this.Vs,
          s = this.fs;
        if (t.embedded)
          try {
            const e = document.getElementById(t.targetElement);
            this.embedInElement(t.targetElement),
              this.updateFullScreenWidth(`${e.clientWidth}px`),
              window.addEventListener(
                "resize",
                An(() => {
                  this.updateFullScreenWidth(`${e.clientWidth}px`);
                }, 500)
              );
          } catch (e) {
            this.di.error("Target Element not specified", e);
          }
        else if (t.sidepanel)
          try {
            const e = document.getElementById(t.targetElement),
              i = e.parentNode,
              o = s.createDiv(["sidepanel-content-wrapper"]);
            i.replaceChild(o, e),
              s.addCSSClass(this.chatWidgetDiv, "sidepanel"),
              o.appendChild(e),
              o.appendChild(this.chatWidgetWrapper);
          } catch (e) {
            this.di.error("Target Element not specified", e);
          }
        else {
          try {
            this.appendToElement(document.body);
          } catch (e) {
            return void this.di.error(
              "Initialisation failed as page is not completely loaded. Make sure to initialise the SDK after document.body is available."
            );
          }
          la(() => {
            this.orientWidgetAnimation();
          }, 0),
            window.addEventListener(
              "resize",
              An(() => {
                this.orientWidgetAnimation();
              }, 500)
            );
          const s = t.width,
            i = t.height;
          s && this.setWidth(s),
            i && this.setHeight(i),
            t.openChatOnLoad &&
              la(
                null === (e = this.wh) || void 0 === e ? void 0 : e.bind(this),
                0
              );
        }
      }
      gl(e) {
        var t;
        this.Vs.searchBarMode
          ? this.sh.appendMessageToConversation(e)
          : this.wn.appendChild(e),
          (null === (t = this.Vn) || void 0 === t ? void 0 : t.isVisible()) &&
            (this.hideTypingIndicator(), this.showTypingIndicator());
      }
      Uc() {
        const e = this.Fl.element;
        la(() => {
          e && (e.scrollTop = e.scrollHeight);
        }, gi.CHAT_SCROLL_DELAY);
      }
      Al(e, t = !0) {
        if (!(null == e ? void 0 : e.length)) return Promise.resolve();
        const s = e.filter((e) => vt(e)),
          i = this.Vs.threadId,
          o = s.filter((e) => !e.threadId || !i || e.threadId === i);
        return o.length
          ? new Promise((e) => {
              const s = { isFresh: t };
              this.Vs.clientAuthEnabled && this.Vs.enableAttachmentSecurity
                ? this.ca
                    .getAuthToken()
                    .then((t) => {
                      (s.authToken = t.token), this.Nl(o, s), e(), this.Uc();
                    })
                    .catch(() => {
                      this.Nl(o, s), e(), this.Uc();
                    })
                : (this.Nl(o, s), e(), this.Uc());
            })
          : Promise.resolve();
      }
      Dl(e, t) {
        var s, i, o, r;
        let a;
        if (cr(e)) {
          let n = "";
          if (e.source === Ve) {
            const i = this.Vs.icons;
            (null === (s = e.messagePayload.channelExtensions) || void 0 === s
              ? void 0
              : s.agentSession) ||
              (e.messagePayload.channelExtensions
                ? (e.messagePayload.channelExtensions.agentSession = this.wl)
                : (e.messagePayload.channelExtensions = {
                    agentSession: this.wl,
                  })),
              !this.wl.avatarImage && i.avatarBot && t.appendChild(this.Hl()),
              (n = this.wl.name);
          } else if (
            e.source === Be &&
            (null === (i = e.messagePayload.channelExtensions) || void 0 === i
              ? void 0
              : i.agentSession)
          ) {
            n = (
              null === (o = e.messagePayload.channelExtensions) || void 0 === o
                ? void 0
                : o.agentSession
            ).name;
          }
          n &&
            ((a = this.fs.createTextDiv(["agent-name"])),
            (a.title = n),
            (a.innerHTML = n),
            a.setAttribute("aria-hidden", "true"),
            (null === (r = this.wl) || void 0 === r
              ? void 0
              : r.nameTextColor) && (a.style.color = this.wl.nameTextColor));
        }
        return a;
      }
      Hl() {
        const e = this.wl || {},
          t = e.name.split(" ").filter((e) => e);
        let s = t[0][0];
        return (
          t.length > 1 && (s += t[t.length - 1][0]),
          this.yl(s.toUpperCase(), e.name, !0)
        );
      }
      vl() {
        if (this.Vs.showTypingIndicator) {
          const e = this.wl || {},
            t = this.Vs.icons,
            s = this.gi;
          t.avatarBot &&
            (!e.avatarImage && e.name
              ? this.Vn.updateTypingCueIcon(this.Hl())
              : this.Vn.updateTypingCueIcon(
                  this.yl(
                    e.avatarImage || t.avatarBot,
                    s.avatarAgent || s.avatarBot
                  )
                ));
        }
      }
      yl(e, t, s = !1) {
        const i = this.fs,
          o = i.createDiv(["icon-wrapper", s ? "agent-avatar" : ""]),
          r = this.wl || {};
        let a;
        return (
          s
            ? ((a = i.createTextDiv(["agent-icon"])),
              (a.innerText = e),
              this.Th === ca && i.addCSSClass(this.Un.element, "left"),
              r.avatarTextColor && (a.style.color = r.avatarTextColor),
              r.avatarBackgroundColor &&
                (o.style.background = r.avatarBackgroundColor))
            : (a = i.createImageIcon({ icon: e, iconCss: ["message-icon"] })),
          o.appendChild(a),
          o.setAttribute("aria-label", t),
          o
        );
      }
      Ul(e) {
        const t = e ? new Date(e) : new Date(),
          s = Y(t, { pattern: this.Vs.timestampFormat, locale: this.Ch }),
          i = this.fs.createTextDiv(["message-date"]);
        return (
          i.setAttribute("aria-live", "off"),
          i.setAttribute("aria-hidden", "true"),
          (i.innerText = `${s}`),
          i
        );
      }
      Nl(e, t) {
        var s;
        const { isFresh: i, authToken: o } = t,
          r = this.Vs,
          a = this.fs,
          n = Object.assign(Object.assign({}, this.Mh), {
            locale: this.Ch,
            isFresh: i,
          });
        (null == o ? void 0 : o.length) && ((n.authToken = o), (n.uri = r.URI));
        const c =
          p(null === (s = r.delegate) || void 0 === s ? void 0 : s.onMessage) &&
          r.delegate.onMessage;
        e.forEach((e) => {
          var t, s, o, h, l, p, d, u;
          const g = cr(e);
          if (g) {
            const t = hr(e);
            if (this.mc.includes(t)) return;
            this.mc.push(t);
          }
          const m = pr.fromMessage(r, a, e, n);
          if (!m) return;
          if (c)
            return void c(m.render(), { isNewMessage: i, isUserMessage: !g });
          if (m instanceof ir) {
            this.Vl = e;
            const t = e.messagePayload;
            switch (t.streamState) {
              case "start":
                this.Un.disable(), (this.hl = m), this.Bl();
                break;
              case "running":
                if (this.hl) return this.hl.update(t), void this.Bl();
                this.Un.disable(), (this.hl = m);
                break;
              case "end":
                if ((clearTimeout(this.Wl), this.Un.disable(!1), this.hl))
                  return (
                    this.hl.update(t), (this.hl = null), void (this.Vl = null)
                  );
            }
          } else
            this.hl && this.Un.disable(!1),
              (this.hl = null),
              (this.Vl = null),
              clearTimeout(this.Wl);
          const b = g ? He : Ue,
            f = this.ql(e.messagePayload, b),
            w = this.Zl(e.messagePayload);
          if (((f || w) && this.Gl(), w)) {
            const i = this.skillMessages.at(-1);
            if (i)
              return (
                this.ac.push(i),
                i.append(m),
                this.Vc([i]),
                (m.msgId = e.msgId),
                (this.il = b),
                (this.Ic = Date.now()),
                (this.bc =
                  0 !==
                  (null === (t = e.messagePayload.globalActions) || void 0 === t
                    ? void 0
                    : t.length)),
                (this.Yl =
                  (null ===
                    (o =
                      null === (s = e.messagePayload.channelExtensions) ||
                      void 0 === s
                        ? void 0
                        : s.agentSession) || void 0 === o
                    ? void 0
                    : o.name) || ""),
                (this.Jl = e.source),
                this.Hh(m),
                void this.Rh(He)
              );
          }
          const v = f || this.Kl(e, b);
          let x;
          if (
            ((m.msgId = e.msgId),
            (this.il = b),
            (this.Ic = Date.now()),
            (this.bc =
              e.messagePayload.globalActions &&
              0 !== e.messagePayload.globalActions.length),
            (this.Yl =
              (null ===
                (l =
                  null === (h = e.messagePayload.channelExtensions) ||
                  void 0 === h
                    ? void 0
                    : h.agentSession) || void 0 === l
                ? void 0
                : l.name) || ""),
            g && (this.Jl = e.source),
            v || ((x = a.createDiv(["message-block", "flex"])), (this.Xl = x)),
            void 0 !== m.ratingId && (this.Ql = m),
            g)
          )
            this.nc && this.ep(m),
              this.skillMessages.push(m),
              e.source === Ve
                ? ((null === (p = e.messagePayload.channelExtensions) ||
                  void 0 === p
                    ? void 0
                    : p.agentName) &&
                    this.setAgentDetails({
                      name: e.messagePayload.channelExtensions.agentName,
                      avatarImage: r.icons.avatarAgent,
                      nameTextColor: null,
                      avatarTextColor: null,
                      avatarBackgroundColor: null,
                    }),
                  (null === (d = e.messagePayload.channelExtensions) ||
                  void 0 === d
                    ? void 0
                    : d.agentSession) &&
                    this.setAgentDetails(
                      e.messagePayload.channelExtensions.agentSession
                    ))
                : (this.Zc.removeItem(this.xl), (this.wl = null)),
              this.Hh(m);
          else if (this.Ql) {
            const t = e;
            if (
              t.messagePayload.type === Oe.Text ||
              t.messagePayload.type === Oe.Postback
            ) {
              const e = t.messagePayload;
              this.Ql.highlightRating(e.text);
            }
            this.Ql = null;
          }
          if (r.searchBarMode) return void this.sh.renderMessage(e, m, f);
          const k =
            r.useCreatedOnTimestamp && e.createdOn
              ? new Date(e.createdOn)
              : e.date
              ? new Date(e.date)
              : new Date();
          this.ul(k), x && (this.tp(e, x), this.gl(x));
          const y = this.Xl.querySelector('[class*="message-list"]'),
            z = this.Kn(e, m, y);
          if (z) {
            if (e.messagePayload.type === Oe.Card) {
              const e = y.querySelectorAll('[class*="message-bubble"]');
              if (e.length) {
                e[e.length - 1].classList.add(`${this.Xi}-before-card`);
              }
            }
            f && y.lastElementChild
              ? (this.mh(),
                this.isOpen || this.updateNotificationBadge(--this.rc),
                null === (u = y.lastElementChild) ||
                  void 0 === u ||
                  u.replaceWith(z),
                this.ac.push(m))
              : y.appendChild(z),
              m instanceof Fo && m.setCardsScrollAttributes(this.Th);
          }
          this.Rh(b);
        });
      }
      Bl() {
        clearTimeout(this.Wl),
          (this.Wl = la(() => {
            this.Un.disable(!1),
              this.hl &&
                this.hl.update(
                  Object.assign(Object.assign({}, this.Vl.messagePayload), {
                    streamState: "end",
                  })
                ),
              (this.hl = null),
              (this.Vl = null),
              this.hideTypingIndicator();
          }, this.fc));
      }
      Zl(e) {
        var t;
        const s =
          null === (t = e.channelExtensions) || void 0 === t
            ? void 0
            : t.appendMessage;
        return "True" === s || s;
      }
      ql(e, t) {
        var s;
        if (t === He) {
          const t = e.channelExtensions,
            i = null == t ? void 0 : t.replaceMessage,
            o =
              null === (s = null == t ? void 0 : t.websdk) || void 0 === s
                ? void 0
                : s.replaceMessage;
          return At(i) || At(o);
        }
        return !1;
      }
      Kl(e, t) {
        var s, i;
        if (!(Date.now() - this.Ic < 1e4)) return !1;
        if (
          cr(e) &&
          e.source === Ve &&
          (null === (s = e.messagePayload.channelExtensions) || void 0 === s
            ? void 0
            : s.agentSession)
        ) {
          const t =
            null === (i = e.messagePayload.channelExtensions) || void 0 === i
              ? void 0
              : i.agentSession;
          return this.Yl === t.name;
        }
        return !(this.il !== t || (cr(e) && e.source !== this.Jl) || this.bc);
      }
      Gl() {
        var e;
        if (
          !(null === (e = this.wn) || void 0 === e
            ? void 0
            : e.lastElementChild)
        )
          return;
        const { name: t } = this.Vs,
          s = `${t}-message-block`,
          i = `${t}-left`;
        let o = this.wn.lastElementChild;
        for (o && (o = o.previousElementSibling); o; ) {
          const e = o.previousElementSibling;
          if (o.classList.contains(s)) {
            if (o.classList.contains(i)) {
              this.Xl = o;
              break;
            }
            o.remove();
          }
          o = e;
        }
      }
      tp(e, t) {
        const s = this.Vs.icons,
          i = this.gi,
          o = this.fs,
          r = this.wl || {};
        let a, n, c;
        if (cr(e)) {
          if (
            ((a = this.Dl(e, t)),
            e.source === Ve
              ? ((n =
                  s.avatarBot &&
                  (r.avatarImage || !r.name) &&
                  (r.avatarImage || s.avatarAgent || s.avatarBot)),
                (c = i.agentMessage.replace("{0}", `${r.name || i.agent}`)))
              : (this.Jl === Ve &&
                  this.Vs.showTypingIndicator &&
                  this.Vn.resetTypingCueIcon(),
                (n = s.avatarBot),
                (c = i.skillMessage)),
            o.addCSSClass(t, "left"),
            n)
          ) {
            this.Th === ca && o.addCSSClass(this.Un.element, "left");
            const s = this.yl(
              n,
              (e.source === Ve && i.avatarAgent) || i.avatarBot
            );
            (s.style.marginTop = a && "16px"), t.appendChild(s);
          }
        } else
          o.addCSSClass(t, "right"),
            (c = i.userMessage),
            s.avatarUser &&
              (this.Th === ca && o.addCSSClass(this.Un.element, "right"),
              t.appendChild(this.yl(s.avatarUser, i.avatarUser)));
        const h = o.createDiv(["messages-wrapper", "flex", "col"]);
        a && h.appendChild(a);
        const l = this.fs.createTextSpan(["screen-reader-only"]);
        (l.innerText = c), h.appendChild(l);
        const p = o.createDiv(["message-list", "flex", "col"]);
        if ((h.appendChild(p), "absolute" === this.Vs.timestampMode)) {
          const t =
              this.Vs.useCreatedOnTimestamp && e.createdOn
                ? new Date(e.createdOn).getTime()
                : e.date,
            s = this.Ul(t);
          h.appendChild(s);
        }
        t.appendChild(h);
      }
      Kn(e, t, s) {
        const i = this.Vs.delegate;
        if (i && i.render) {
          const t = this.fs.createDiv(["message"]);
          (t.id = e.msgId), (t.lang = this.Ch), s.appendChild(t);
          if (i.render(e)) return null;
          t.remove();
        }
        return t.render();
      }
      ul(e) {
        "none" !== this.Vs.timestampHeaderMode &&
          (((e, t) => {
            const s = new Date(e),
              i = new Date(t);
            return (
              s.getDate() === i.getDate() &&
              s.getMonth() === i.getMonth() &&
              s.getFullYear() === i.getFullYear()
            );
          })(this.Cl, e) ||
            ((this.Cl = new Date(e)), this.gl(this.sp(this.Cl))));
      }
      sp(e, t = !0) {
        const s = this.fs,
          i = s.createDiv(["timestamp-container"]),
          o = s.createTextDiv(["timestamp-header"]),
          r = { pattern: this.Vs.timestampHeaderFormat, locale: this.Ch };
        if (
          ((o.textContent =
            "relative" === this.Vs.timestampHeaderMode
              ? ((e, t) => {
                  var s, i;
                  const o =
                      null !== (s = null == t ? void 0 : t.locale) &&
                      void 0 !== s
                        ? s
                        : "en",
                    r = new Date(e),
                    a = new Date(),
                    n = J(a, r);
                  if (0 === n || -1 === n) return Q(r, n, o);
                  const c =
                    null !== (i = null == t ? void 0 : t.pattern) &&
                    void 0 !== i
                      ? i
                      : {
                          weekday: "short",
                          month: "short",
                          day: "numeric",
                          hour: "numeric",
                          minute: "numeric",
                          hour12: !0,
                        };
                  return Y(r, { pattern: c, locale: o });
                })(e, r)
              : Y(e, r)),
          (this.$l = o),
          i.append(o),
          t)
        ) {
          const e = s.createElement("hr", ["conversation-separator"], !1);
          i.append(e);
        }
        return i;
      }
      Rh(e) {
        this.ip || (this.ip = this.Dh.render()),
          this.ip.remove(),
          this.Dh.refresh(e),
          this.gl(this.ip);
      }
      Hh(e) {
        e.hasActions() &&
          la(() => {
            e.focusFirstAction();
          }, 290);
      }
      jl(e, t, s) {
        const i = document.querySelector(`#${e}`);
        if (i) {
          const e = this.fs.createDiv(s);
          e.appendChild(i), t.appendChild(e);
        } else
          this.di.error(
            `Could not find element with ID '${e}'. No element embedded to the chat conversation pane.`
          );
      }
      onSpeechToggle(e) {
        this.mh(), this.Ko.trigger(ui.CLICK_VOICE_TOGGLE, e), this.op(e);
      }
      Yh() {
        this.op(!1);
      }
      Fh() {
        this.op(!0);
      }
      op(e) {
        const t = this.gi;
        this.Vs.enableSpeech &&
          (e
            ? (this.rp(),
              this.Vs.speechLocale && !ke(this.Vs.speechLocale)
                ? this.jc(t.errorSpeechUnsupportedLocale, sn)
                : this.ca.startRecognition().catch(this.oh))
            : (this.ca.stopRecognition(), this.Un.setVoiceRecording(!1)));
      }
      ah(e) {
        if (e)
          switch (e.type) {
            case "partial":
              let t = e.text;
              t.length > 0 &&
                (this.speechFinalResult &&
                  (t = `${this.speechFinalResult.text} ${t}`),
                this.Un.setUserInputText(t));
              break;
            case "final":
              let s = e.text;
              s.length > 0
                ? (this.speechFinalResult &&
                    (s = `${this.speechFinalResult.text} ${s}`),
                  this.Un.setUserInputText(s),
                  this.Vs.enableSpeechAutoSend
                    ? la(() => {
                        const t = Qe(s, e.requestId);
                        this.sendMessage(t)
                          .then(() => {
                            var e;
                            this.Un.setUserInputText(""),
                              null === (e = this.sh) ||
                                void 0 === e ||
                                e.openPopup();
                          })
                          .catch(this.Yc);
                      }, 200)
                    : (this.speechFinalResult = {
                        speechId: e.requestId,
                        text: s,
                      }))
                : this.speechFinalResult &&
                  this.Un.setUserInputText(this.speechFinalResult.text);
              break;
            case "error":
              this.oh(new Error(e.text));
          }
      }
      Hc(e) {
        switch (this.Vs.disablePastActions) {
          case "all":
            e.forEach((e) => {
              e.disableActions();
            });
            break;
          case "postback":
            e.forEach((e) => {
              e.disablePostbacks();
            });
        }
      }
      Vc(e) {
        switch (this.Vs.disablePastActions) {
          case "all":
            e.forEach((e) => {
              e.enableActions();
            });
            break;
          case "postback":
            e.forEach((e) => {
              e.enablePostbacks();
            });
        }
      }
      ap() {
        this.Hc(this.skillMessages);
      }
      ep(e) {
        "none" !== this.Vs.disablePastActions && this.ac.push(e);
      }
      ll() {
        var e;
        this.Hc(this.ac),
          (this.ac = []),
          null === (e = this.Eh) || void 0 === e || e.show();
      }
      Mc() {
        ("none" === this.Vs.disablePastActions
          ? this.skillMessages
          : this.ac
        ).forEach((e) => {
          e.enablePostbacks();
        });
      }
      $c() {
        ("none" === this.Vs.disablePastActions
          ? this.skillMessages
          : this.ac
        ).forEach((e) => {
          e.disablePostbacks();
        });
      }
      tl(e = !1) {
        var t;
        const s = this.Vs.searchBarMode ? this.Bh : this.wn;
        let i = !1;
        for (
          (null === (t = this.Vn) || void 0 === t ? void 0 : t.isVisible()) &&
          ((i = !0), this.hideTypingIndicator());
          s.firstChild;

        )
          s.removeChild(s.lastChild);
        i && this.showTypingIndicator(),
          (this.uc = !0),
          (this.Cl = null),
          this.mh(),
          e ? (this.dc = !0) : this.Ko.trigger(ui.CLICK_ERASE);
      }
      Ah() {
        const { userId: e, channelId: t } = this.Vs;
        ra &&
          (this.zc(),
          (this.np = new ra(`${e}-${t}`)),
          (this.np.onmessage = this.cp.bind(this)));
      }
      zc() {
        this.np && (this.np.close(), (this.np = null));
      }
      hp(e) {
        if (this.np) {
          const t = { type: "message", message: e };
          if (cr(e)) {
            const s = hr(e);
            if (this.mc.includes(s)) return;
            t.digest = s;
          }
          this.np.postMessage(t);
        }
      }
      sl(e) {
        this.np && this.np.postMessage(e);
      }
      cp(e) {
        var t, s, i, o;
        const r = e.data;
        switch (r.type) {
          case "message":
            const e = r.message.messagePayload;
            if (e.type === Oe.Status) {
              const t = e;
              return void ("RESPONDING" === t.status
                ? this.showTypingIndicator()
                : "LISTENING" === t.status && this.hideTypingIndicator());
            }
            if (e.type === Oe.SessionClosed)
              return void (
                null === (t = this.kh) ||
                void 0 === t ||
                t.call(this)
              );
            if (r.digest) {
              if (this.mc.includes(r.digest)) return;
              null === (s = this.yh) || void 0 === s || s.call(this, r.message);
            } else
              null === (i = this.zh) || void 0 === i || i.call(this, r.message),
                this.ll(),
                this.showTypingIndicator();
            this.Vs.searchBarMode || this.hideTypingIndicator(),
              this.Al([r.message]);
            break;
          case "actionClearHistory":
            this.tl();
            break;
          case "actionLanguage":
            null === (o = this.Sc) || void 0 === o || o.setTag(r.tag, !1);
        }
      }
      Nh() {
        if (
          this.Vs.wcfsEnableEndConversationButtonToClose &&
          this.ca.getState() === r
        )
          this.kh();
        else {
          const e = this.gi;
          this.rp();
          const t = new vi({
            title: e.endConversationConfirmMessage || "",
            description: e.endConversationDescription || "",
            parent: this.chatWidgetDiv,
            domUtil: this.fs,
            actions: [
              { label: e.noText, handler: this.rp.bind(this) },
              { label: e.yesText, handler: this.lp.bind(this), type: "filled" },
            ],
          });
          t.open(), (this.pp = t);
        }
      }
      lp() {
        this.sendExitEvent(), this.rp();
      }
      jc(e, t, s = 1e4) {
        this.rp();
        const i = new vi({
          title: e,
          icon: t,
          parent: this.Vs.searchBarMode ? this.Bh : this.chatWidgetDiv,
          domUtil: this.fs,
          fallbackFocus: () => {
            this.Un.focusTextArea();
          },
          showDismiss: !0,
          autoDismiss: !0,
          autoDismissTimeout: s,
          dismissLabel: this.gi.webViewErrorInfoDismiss,
          modeless: !0,
        });
        i.open(), (this.pp = i);
      }
      rp() {
        this.pp && (this.pp.close(), (this.pp = void 0));
      }
      Oh(e = !0) {
        clearTimeout(this._l),
          clearInterval(this.El),
          clearTimeout(this.Ol),
          this.Vs.showTypingIndicator &&
            (e
              ? (this.hideTypingIndicator(),
                this.Vn.setAutoTimeout(!0),
                this.cc && this.Vs.enableVoiceOnlyMode && this.Fh())
              : (this.Vn.setAutoTimeout(!1), this.showTypingIndicator()));
      }
      Lh(e) {
        var t, s;
        const i = this.Vs.delegate;
        if (
          (this.di.debug("onMessageReceived", e),
          this.Uc(),
          (this.gc = !0),
          (this.uc = !1),
          this.Vs.enableDefaultClientResponse &&
            (e.source === Ve ? (this.Ih = !1) : this.Ih || (this.Ih = !0)),
          e)
        ) {
          if (
            i &&
            i.beforeDisplay &&
            p(i.beforeDisplay) &&
            ((e) => {
              let t = !0;
              const s = e.messagePayload;
              s && s.type === Oe.TextStream && (t = !1);
              return t;
            })(e)
          ) {
            let t = d(e);
            try {
              t = i.beforeDisplay(t);
            } catch (e) {
              this.di.error(e);
            }
            if (!t) return;
            xt(t)
              ? (e = t)
              : this.di.error(
                  "The generated delegate message is invalid. Displaying original message instead."
                );
          }
          switch (
            (null === (t = this.yh) || void 0 === t || t.call(this, e),
            this.hp(e),
            e.messagePayload.type)
          ) {
            case Oe.Status: {
              const t = e.messagePayload;
              "RESPONDING" === t.status
                ? this.showTypingIndicator()
                : "LISTENING" === t.status && this.hideTypingIndicator();
              break;
            }
            case Oe.SessionClosed:
              null === (s = this.kh) || void 0 === s || s.call(this);
              break;
            case Oe.TextStream:
              this.Al([e]);
              switch (e.messagePayload.streamState) {
                case "start":
                  this.isOpen || this.updateNotificationBadge(++this.rc);
                  break;
                case "end":
                  this.Tl(e), this.zl(e);
              }
              break;
            default:
              this.Al([e]),
                this.Tl(e),
                this.zl(e),
                this.isOpen || this.updateNotificationBadge(++this.rc);
          }
          this.Oh(Boolean(e.endOfTurn));
        }
      }
      dl(e) {
        this.zl(e),
          this.Uc(),
          e &&
            (this.hp(e),
            e.messagePayload &&
              !pa.includes(e.messagePayload.type) &&
              (this.isOpen || this.updateNotificationBadge(++this.rc),
              this.Al([e])));
      }
      Kh(e) {
        e || this.mh(), (this.cc = !e);
      }
      Ph(e) {
        const t = this.sc.filter((t) => t.threadId === e);
        return (
          (this.Vt = e),
          this.ca.setCurrentThreadId(e),
          this.clearConversationHistory(!0),
          this.dp(t, !1)
        );
      }
      Uh() {
        this._c().then(() => {
          const e = this.Zc.getItem(this.kl);
          e && (this.Vs.icons.avatarUser = e);
          const t = this.Zc.getItem(this.xl);
          t && ((this.wl = JSON.parse(t)), this.vl());
        });
      }
      up(e) {
        const t = this.Vs.threadId;
        this.sc = e.filter((e) => vt(e));
        const s = this.sc,
          i = t ? s.filter((e) => e.threadId === t) : s;
        return this.dp(i);
      }
      loadPreviousConversations() {
        return oa(this, void 0, void 0, function* () {
          const e = this.Vs;
          if (e.storageType === mr.CUSTOM) {
            const t = e.conversationHistoryProvider;
            p(null == t ? void 0 : t.getMessages)
              ? t
                  .getMessages({ threadId: e.threadId })
                  .then((e) => {
                    this.up(e.messages);
                  })
                  .catch((e) =>
                    this.di.error(
                      "Failed to fetch conversation history with provider.",
                      e
                    )
                  )
              : this.di.warn(
                  "Can not load conversation history. Pass conversationHistoryProvider object with getMessages function when custom storage is enabled."
                );
          } else
            e.enableLocalConversationHistory &&
              (this.Vs.clientAuthEnabled && !this.Gc
                ? this._c().then(() => {
                    this.up(this.getMessages());
                  })
                : this.up(this.getMessages()));
          Promise.resolve();
        });
      }
      dp(e) {
        return oa(this, arguments, void 0, function* (e, t = !0) {
          if (e.length)
            return (
              (this.nc = !1),
              this.Al(e.slice(), !1).then(() => {
                (this.nc = !0),
                  t || this.il !== He
                    ? this.ap()
                    : this.Hc(
                        this.skillMessages.slice(
                          0,
                          this.skillMessages.length - 1
                        )
                      ),
                  this.Vs.searchBarMode ||
                    (!t && !this.dc) ||
                    (this.Dh &&
                      (this.Dh.setRelativeTime(new Date(e[e.length - 1].date)),
                      (this.ip = this.Dh.render()),
                      this.gl(this.ip)),
                    this.Vs.showPrevConvStatus &&
                      ((this.Sl = this.fs.createTextDiv(["hr", "flex"])),
                      (this.Sl.innerText = this.gi.previousChats),
                      this.gl(this.Sl)),
                    this.dc && (this.dc = !1));
              })
            );
        });
      }
      Oc() {
        var e;
        if (
          this.ca.isConnected() &&
          this.lc &&
          (this.Sc && (this.Sc.disableComponent(!1), this.Sc.initLanguage()),
          !this.hc)
        ) {
          const t = this.Vs.initUserProfile;
          if (t) {
            const e = this.Vs.sdkMetadata
              ? Object.assign({ version: mi }, this.Vs.sdkMetadata)
              : { version: mi };
            this.ca
              .updateUser(t, { sdkMetadata: e })
              .then(() => {
                this.hc = !0;
              })
              .catch((e) => {
                this.di.error(
                  "[sendInitMessages] Failed to update user profile:",
                  e
                );
              });
          }
          if (this.Vs.initUserHiddenMessage) {
            const e = this.Vs.initUserHiddenMessage;
            this.sendMessage(e, { hidden: !0, delegate: !1 })
              .then(() => {
                this.hc = !0;
              })
              .catch(this.Yc);
          }
          if (
            null === (e = this.Vs.deviceToken) || void 0 === e
              ? void 0
              : e.length
          ) {
            const e = S() ? "android" : I() ? "ios" : "desktop";
            this.ca
              .sendDeviceToken(this.Vs.deviceToken, this.Vs.deviceType || e)
              .then(() => {
                this.hc = !0;
              })
              .catch((e) => {
                this.di.error(
                  "[sendInitMessages] Failed to send device token:",
                  e
                );
              });
          }
        }
      }
      Tl(e) {
        this.cc || this.ca.speakTTS(e, this.gi);
      }
      mh() {
        this.ca.cancelTTS();
      }
      sendUserTypingStatusMessage(e, t) {
        this.getAgentDetails() &&
          this.ca.sendUserTypingStatus(e, t).catch((e) => {
            this.di.error(
              "[sendUserTypingStatusMessage] Failed to send user typing status:",
              e
            );
          });
      }
      Zh(e) {
        if (e.hotkeys) {
          const t = new ur(e);
          t.setWidget(this.chatWidgetDiv);
          const s = e.hotkeys;
          Object.keys(s).forEach((e) => {
            const i = this.wc.get(e);
            i && t.add(s[e], i, "launch" !== e);
          }),
            (this.Qh = t);
        }
      }
      al(e, t) {
        const s = document.getElementsByClassName(`${this.Xi}-${e}`);
        for (const e of Array.from(s))
          for (const [s, i] of Object.entries(t)) e.style[s] = i;
      }
      bh() {
        try {
          sessionStorage.setItem(this.Pl, Array.from(this.gh).toString());
        } catch (e) {
          this.di.warn("Failed to save canceled requests in session", e);
        }
      }
      Ll() {
        try {
          const e = sessionStorage.getItem(this.Pl);
          return e ? e.split(",") : [];
        } catch (e) {
          return (
            this.di.warn("Failed to save canceled requests in session", e), []
          );
        }
      }
      fh() {
        const e = d(this.Vl);
        e &&
          cr(e) &&
          ((e.messagePayload.text = this.hl.freeze()),
          (e.messagePayload.streamState = "end"),
          (e.endOfTurn = !0),
          this.Lh(e));
      }
      setHotkeyMap(e, t) {
        this.wc.set(e, t);
      }
    }
    const ga = () => Promise.reject(Error("TextStreamProgress")),
      ma = "none",
      ba = "full-size";
    class fa extends Pi {
      constructor(e, t, s, i, o, r, a, n, c) {
        super(),
          (this.Vs = e),
          (this.gp = t),
          (this.mp = s),
          (this.bp = i),
          (this.fp = o),
          (this.wp = r),
          (this.ca = a),
          (this.In = n),
          (this.Ko = c),
          (this.di = new ar("ContextualWidgetComponent")),
          (this.vp = !1),
          (this.xp = (e) => {
            switch (e.type) {
              case $e.Postback:
                e.getPayload().then((t) => {
                  (null == t ? void 0 : t.generate)
                    ? this.kp(
                        Object.assign(
                          Object.assign({}, Pn(t.fieldInputParameters)),
                          t.additionalInputParameters
                        )
                      )
                    : (null == t ? void 0 : t.showMore)
                    ? this.showFullSizeWidget()
                    : this.sendMessage(
                        et({ postback: t, text: e.label, type: Oe.Postback })
                      );
                });
                break;
              case $e.SubmitForm:
                const t = e.messageComponent;
                if (!t.validateForm()) break;
                e.getPayload().then((e) => {
                  const s = {
                    postback: e,
                    submittedFields: t.getSubmittedFields(),
                    type: Oe.FormSubmission,
                  };
                  e || delete s.postback, this.sendMessage(tt(s));
                });
            }
          }),
          (this.Xi = e.name),
          (this.Ds = {
            type: Oe.Text,
            text: "",
            globalActions: [
              { type: $e.Postback, label: "Global1", postback: {} },
              { type: $e.Postback, label: "Global2", postback: {} },
              { type: $e.Postback, label: "Global3", postback: {} },
              { type: $e.Postback, label: "Global4", postback: {} },
            ],
          }),
          (this.threadId = `${Pe.UIWidget}:${this.bp || ""}-${this.mp || ""}`),
          (this.yp = this.Vs.sdkMetadata
            ? Object.assign({ version: mi }, this.Vs.sdkMetadata)
            : { version: mi }),
          (this.Vs.icons = Object.assign(Object.assign({}, this.Vs.icons), {
            logo: ln,
          })),
          (this.gi = Object.assign(
            Object.assign({}, this.Vs.i18n.en),
            this.Vs.i18n[this.Vs.locale]
          ));
        const {
          uploadFile: h,
          getSuggestions: l,
          onSpeechToggle: p,
          shareUserLocation: d,
          sendUserTypingStatusMessage: u,
          setHotkeyMap: g,
        } = this.In;
        (this.Un = new Ir(
          t,
          this.sendMessage.bind(this),
          h.bind(n),
          Object.assign(Object.assign({}, this.Vs), { enableAttachment: !1 }),
          l.bind(n),
          p.bind(n),
          d.bind(n),
          u.bind(n),
          this.Ko,
          n,
          g.bind(n)
        )),
          (this.contextualElem = document.getElementById(this.mp)),
          (this.zp = this.contextualElem.querySelector("input, textarea")),
          (this.$p = [
            {
              type: $e.Postback,
              label: "Show more",
              postback: { showMore: !0 },
            },
          ]),
          (this.Cp = !1),
          (this.Sp = !1),
          (this.Ip = !1),
          (this.Mp = !0),
          (this.Mh = { webCore: a, onMessageActionClicked: this.xp });
      }
      render() {
        const e = this.gp,
          t = e.createDiv(["widget-wrapper"]);
        (this.element = e.createDiv(["contextual-widget"])),
          (this.element.id = this.threadId);
        const s = e.createDiv(["container", "none"]);
        this.appendToElement(s), t.appendChild(s), (this.Tp = s);
        const i = this.contextualElem.parentNode,
          o = e.createDiv(["contextual-widget-wrapper"]);
        i.replaceChild(o, this.contextualElem),
          o.appendChild(this.contextualElem),
          document.body.appendChild(t),
          this.contextualElem.parentElement.insertBefore(
            t,
            this.contextualElem
          );
        const r = e.createDiv([]);
        (this.Ap = e.createDiv(["widget", "flex", "col"])),
          this.Ap.setAttribute("role", "region"),
          this.Ap.setAttribute("aria-labelledby", `${this.Xi}-title`);
        const a = e.createDiv(["header", "flex"]),
          n = e.createDiv(["header-info-wrapper"]),
          c = this.gi.chatTitle,
          h = this.Vs.icons;
        if (!("logo" in h) || h.logo) {
          const t = e.createImageIcon({
            icon: h.logo || Va,
            iconCss: ["logo"],
          });
          a.appendChild(t);
        }
        if (c) {
          const t = e.createTextDiv(["title"]);
          (t.id = `${this.Xi}-contextual-title`),
            (t.innerText = c),
            (t.title = c),
            n.appendChild(t);
        }
        a.appendChild(n);
        const l = e.createIconButton({
          css: ["start-over-button", ma],
          icon: dn,
          iconCss: [],
          title: "Start Again",
        });
        (l.onclick = () => {
          this.zp
            ? (this.zp.value = "")
            : this.di.error(
                "The input element is not found for clearing the filled-in text."
              ),
            (this.Mp = !0),
            (this.vp = !0),
            e.addCSSClass(l, ma),
            this._p();
        }),
          a.appendChild(l),
          (this.Ep = l);
        const p = e.createIconButton({
          css: ["close-button"],
          icon: h.close || _a,
          iconCss: [],
          title: "close",
        });
        (p.onclick = this.Op.bind(this)),
          a.appendChild(p),
          this.Ap.appendChild(a),
          (this.Ln = e.createDiv(["widget-content"])),
          this.Ap.appendChild(this.Ln),
          this.Un.render(),
          this.Un.disable(!1),
          this.Ap.appendChild(this.Un.element),
          e.addCSSClass(r, "open"),
          r.appendChild(this.Ap),
          e.addCSSClass(this.element, "wrapper", this.Vs.theme),
          this.element.appendChild(r),
          this.Ds.globalActions && (this.Pp = this.Ds.globalActions),
          this.Lp(!0);
      }
      sendMessage(e, t = !0) {
        return this.hl
          ? ga()
          : ("string" == typeof e && (e = Qe(e)),
            this.Un.focusTextArea(),
            e &&
              this.ca
                .sendMessage(e, {
                  sdkMetadata: this.yp,
                  threadId: this.threadId,
                })
                .then(() => {
                  (this.Ip = !1),
                    this.gp.removeCSSClass(this.Ep, ma),
                    t && this.jp();
                })
                .catch((e) =>
                  this.di.error("[sendMessage] Failed to send message:", e)
                ));
      }
      onMessageReceived(e) {
        var t, s;
        const i = this.Vs,
          o = this.zp,
          r = this.gp;
        if (
          ((this.Sp = !1),
          this.Cp ||
            (r.addCSSClass(this.Un.element, "enabled"), (this.Cp = !0)),
          e.messagePayload.llmGenerated)
        ) {
          const t = pr.fromMessage(i, r, e, this.Mh);
          if (!t) return;
          if (((this.Ip = !0), t instanceof ir)) {
            const s = e.messagePayload;
            switch (s.streamState) {
              case "start":
                return (
                  this.Un.disable(),
                  (t.isCoPilot = !0),
                  (t.showDone = this.Fp.bind(this)),
                  void (this.Rp
                    ? this.Rp(s)
                    : o
                    ? ((t.textElement = o), t.update(s), (this.hl = t))
                    : this.di.error(
                        "The input element is not found for filling in the generated text."
                      ))
                );
              case "running":
                return void (this.Rp ? this.Rp(s) : this.hl.update(s));
              case "end":
                this.Un.disable(!1),
                  this.Rp
                    ? (this.Rp(s), this.Fp())
                    : (this.hl.update(s), (this.hl = null)),
                  (this.Mp = !1),
                  (s.text = ""),
                  this.Kn(e);
            }
          } else if (((this.hl = null), (this.Mp = !1), t instanceof Ro)) {
            const t = e.messagePayload;
            this.Rp
              ? this.Rp(t)
              : ((o.innerHTML = zn(t.text)), (t.text = ""), this.Kn(e)),
              this.Op();
          }
        } else if (
          null === (t = e.messagePayload.channelExtensions) || void 0 === t
            ? void 0
            : t.showInDialog
        ) {
          const t = r.createDiv(["wrapper", "popup-content-wrapper"]),
            s = r.createDiv(["popup-dialog"]),
            o = pr.fromMessage(i, r, e, this.Mh);
          s.appendChild(o.render()), t.appendChild(s);
          const a = o.actionsWrapper;
          if (a) {
            const e = a.children;
            for (let s = 0; s < e.length; s++)
              e[s].addEventListener("click", () => t.remove());
          }
          (t.onclick = (e) => {
            s.contains(e.target) || t.remove();
          }),
            document.body.appendChild(t),
            (this.Mp = !1),
            this.Op();
        } else if (((this.Mp = !1), e.messagePayload.type === Oe.Error)) {
          if (
            ((this.Sp = !0),
            null === (s = this.Ln.firstChild) || void 0 === s || s.remove(),
            !this.Np)
          ) {
            const e = r.createDiv(["error-message"]);
            e.appendChild(
              r.createImageIcon({ icon: pn, iconCss: ["error-icon"] })
            );
            const t = r.createDiv(["error-info"]),
              s = r.createTextDiv(["error-text"]),
              i = r.createTextDiv(["reset-button"]);
            (i.onclick = () => {
              (this.Sp = !1), (this.Mp = !0), this._p();
            }),
              (s.innerText = "Something went wrong"),
              (i.innerText = "Start over"),
              t.appendChild(s),
              t.appendChild(i),
              e.appendChild(t),
              (this.Np = e);
          }
          this.Ln.appendChild(this.Np), this._p();
        } else this.Kn(e), this.showFullSizeWidget();
      }
      addText(e) {
        return (this.Ds.text = e), this;
      }
      addAction(e, t, s = !1) {
        return (
          this.$p.push({
            type: $e.Postback,
            label: e,
            postback: { actionId: t, generate: s },
          }),
          this
        );
      }
      addFieldInputParameter(e, t, s) {
        return (
          this.$p.forEach((i) => {
            const o = i.postback;
            o.actionId === e &&
              (o.fieldInputParameters || (o.fieldInputParameters = {}),
              (o.fieldInputParameters[t] = s));
          }),
          this
        );
      }
      addAdditionalInputParameter(e, t, s) {
        return (
          this.$p.forEach((i) => {
            const o = i.postback;
            o.actionId === e &&
              (o.additionalInputParameters ||
                (o.additionalInputParameters = {}),
              (o.additionalInputParameters[t] = s));
          }),
          this
        );
      }
      createWidget() {
        const e = this.contextualElem;
        return (
          this.element || this.render(),
          this.fp &&
            e.addEventListener("focus", () => {
              this.showWidget();
            }),
          this
        );
      }
      showWidget() {
        const e = this.wp;
        return (
          Object.keys(e)
            .filter((e) => e !== this.threadId)
            .forEach((t) => {
              e[t].hideWidget();
            }),
          this.gp.removeCSSClass(this.Tp, ma),
          this
        );
      }
      collapseWidget() {
        return this.Op(), this;
      }
      hideWidget() {
        return this.gp.addCSSClass(this.Tp, ma), this;
      }
      startWidgetInteraction(e) {
        return this.kp(this.Dp(e)), this;
      }
      onGeneratedText(e) {
        return (this.Rp = e), this;
      }
      Kn(e) {
        var t;
        const s = pr.fromMessage(
          Object.assign(Object.assign({}, this.Vs), {
            actionsLayout: "horizontal",
            globalActionsLayout: "horizontal",
          }),
          this.gp,
          e,
          this.Mh
        );
        null === (t = this.Ln.firstChild) || void 0 === t || t.remove(),
          this.Ln.appendChild(s.render());
      }
      Lp(e = !1) {
        this.Mp &&
          (e
            ? (1 === this.$p.length
                ? (this.Ds.actions = this.$p.slice(0))
                : (this.Ds.actions = this.$p.slice(0, 2).reverse()),
              (this.Ds.globalActions = []))
            : ((this.Ds.actions = this.$p.slice(1)),
              this.Pp && (this.Ds.globalActions = this.Pp.slice(0))),
          this.Kn({ messagePayload: this.Ds }));
      }
      Op() {
        const e = this.gp;
        if (!this.Hp) {
          const t = e.createDiv([
              "minimum-size",
              "contextual-widget",
              "wrapper",
            ]),
            s = e.createIconButton({
              css: [],
              icon: hn,
              iconCss: [],
              title: "open",
            }),
            i = e.createIconButton({
              css: [],
              icon: cn,
              iconCss: [],
              title: "like",
            }),
            o = e.createIconButton({
              css: [],
              icon: nn,
              iconCss: [],
              title: "dislike",
            });
          (s.onclick = () => {
            this.Mp || this.Sp ? this._p() : this.showFullSizeWidget();
          }),
            (i.onclick = () => {
              this.sendMessage(
                et({
                  postback: { rating: "positive", feedbackType: "llm" },
                  type: $e.Postback,
                }),
                !1
              );
            }),
            (o.onclick = () => {
              this.sendMessage(
                et({
                  postback: { rating: "negative", feedbackType: "llm" },
                  type: $e.Postback,
                }),
                !1
              );
            }),
            t.appendChild(s),
            t.appendChild(i),
            t.appendChild(o),
            this.Tp.appendChild(t),
            (this.Hp = t);
        }
        e.removeCSSClass(this.element, ba),
          e.addCSSClass(this.element, ma),
          this.Up && e.addCSSClass(this.Up, ma),
          this.Vp && e.addCSSClass(this.Vp, ma),
          e.removeCSSClass(this.Hp, ma),
          this.Ip
            ? e.removeCSSClass(this.Hp, "no-feedback")
            : e.addCSSClass(this.Hp, "no-feedback");
      }
      _p() {
        const e = this.gp;
        this.Hp && e.addCSSClass(this.Hp, ma),
          this.Up && e.addCSSClass(this.Up, ma),
          this.Vp && e.addCSSClass(this.Vp, ma),
          e.removeCSSClass(this.element, ba),
          e.removeCSSClass(this.element, ma),
          this.Lp(!0),
          (this.Ip = !1);
      }
      showFullSizeWidget() {
        const e = this.gp;
        this.Hp && e.addCSSClass(this.Hp, ma),
          this.Up && e.addCSSClass(this.Up, ma),
          this.Vp && e.addCSSClass(this.Vp, ma),
          e.addCSSClass(this.element, ma),
          this.Lp(),
          e.addCSSClass(this.element, ba);
      }
      jp() {
        const e = this.gp;
        if (!this.Up) {
          const t = e.createDiv(["generate-spinner"]),
            s = e.createTextDiv(["generate-text"]);
          (s.innerText = "Generating..."),
            t.appendChild(
              e.createImageIcon({
                icon: an,
                iconCss: ["generate-icon", "spin"],
              })
            );
          const i = e.createIconButton({
            css: ["close-button", ma],
            icon: _a,
            iconCss: [],
            title: "close",
          });
          (i.onclick = this.Op.bind(this)),
            t.appendChild(s),
            t.appendChild(i),
            this.Tp.appendChild(t),
            (this.Up = t);
        }
        this.Hp && e.addCSSClass(this.Hp, ma),
          this.Vp && e.addCSSClass(this.Vp, ma),
          e.removeCSSClass(this.element, ba),
          e.addCSSClass(this.element, ma),
          e.removeCSSClass(this.Up, ma);
      }
      Fp() {
        const e = this.gp;
        if (!this.Vp) {
          const t = e.createDiv(["generate-spinner"]),
            s = e.createTextDiv(["generate-text"]);
          (s.innerText = "Done"),
            t.appendChild(
              e.createImageIcon({ icon: rn, iconCss: ["generate-icon"] })
            ),
            t.appendChild(s),
            this.Tp.appendChild(t),
            (this.Vp = t);
        }
        this.Hp && e.addCSSClass(this.Hp, ma),
          e.addCSSClass(this.Up, ma),
          e.removeCSSClass(this.Vp, ma),
          e.removeCSSClass(this.element, ba),
          e.addCSSClass(this.element, ma),
          setTimeout(this.Op.bind(this), 3e3);
      }
      kp(e) {
        this.sendMessage({
          messagePayload: {
            type: Oe.UpdateApplicationContextCommand,
            source: Pe.UIWidget,
            context: this.bp,
            properties: e,
            reset: this.vp,
          },
        });
      }
      Dp(e) {
        let t;
        return (
          this.$p.forEach((s) => {
            const i = s.postback,
              { fieldInputParameters: o, additionalInputParameters: r } = i;
            i.actionId === e &&
              (t = Object.assign(Object.assign({}, Pn(o)), r));
          }),
          t
        );
      }
    }
    const wa = "Please try sharing it again, or else type it in.",
      va = {
        badgePosition: { right: "-5px", top: "-5px" },
        clientAuthEnabled: !1,
        conversationBeginPosition: "bottom",
        disablePastActions: "all",
        displayActionsAsPills: !1,
        searchBarMode: !1,
        sidepanel: !1,
        embedded: !1,
        embeddedVideo: !0,
        enableAgentSneakPreview: !1,
        enableAttachment: !0,
        enableAttachmentSecurity: !1,
        enableHeaderActionCollapse: !0,
        enableAutocomplete: !1,
        enableAutocompleteClientCache: !1,
        enableBotAudioResponse: !1,
        enableCancelResponse: !1,
        enableClearMessage: !1,
        enableDefaultClientResponse: !1,
        enableEmbeddedActions: !0,
        enableEndConversation: !0,
        enableHeadless: !1,
        enableLocalConversationHistory: !1,
        enableLongPolling: !1,
        enableResizableWidget: !1,
        enableSendTypingStatus: !1,
        enableSecureConnection: !0,
        enableSpeech: !1,
        enableSpeechAutoSend: !0,
        enableTabsSync: !0,
        enableVoiceOnlyMode: !1,
        focusOnNewMessage: "input",
        height: "620px",
        i18n: {
          en: {
            agent: "Agent",
            agentMessage: "{0} says",
            attachment_audio: "Audio attachment",
            attachment_file: "File attachment",
            attachment_image: "Image attachment",
            attachment_video: "Video attachment",
            attachmentAudioFallback:
              "Your browser does not support embedded audio. However you can {0}download it{/0}.",
            attachmentVideoFallback:
              "Your browser does not support embedded video. However you can {0}download it{/0}.",
            audioResponseOff: "Turn audio response on",
            audioResponseOn: "Turn audio response off",
            avatarAgent: "Agent icon",
            avatarBot: "Bot icon",
            avatarUser: "User icon",
            cancelResponse: "Cancel response",
            card: "Card {0}",
            cardImagePlaceholder: "Card image",
            cardNavNext: "Next card",
            cardNavPrevious: "Previous card",
            chatTitle: "Chat",
            clear: "Clear conversation",
            close: "Close widget",
            closing: "Closing",
            connected: "Connected",
            connecting: "Connecting",
            connectionFailureMessage:
              "Sorry, the assistant is unavailable right now. If the issue persists, contact your help desk.",
            connectionRetryLabel: "Try Again",
            copyFailureMessage:
              "Sorry, copying is not available on this device.",
            copySuccessMessage:
              "Successfully copied the response text to the clipboard.",
            defaultGreetingMessage:
              "Hey, Nice to meet you! Allow me a moment to get back to you.",
            defaultWaitMessage:
              "I'm still working on your request. Thank you for your patience!",
            defaultSorryMessage:
              "I'm sorry. I can't get you the right content. Please try again.",
            disconnected: "Disconnected",
            download: "Download",
            editFieldErrorMessage: "Field input is invalid",
            editFormErrorMessage: "Some of the fields need your attention",
            endConversation: "End Conversation",
            endConversationConfirmMessage:
              "Are you sure you want to end the conversation?",
            endConversationDescription:
              "This will also clear your conversation history.",
            errorSpeechInvalidUrl:
              "ODA URL for connection is not set. Please pass 'URI' parameter during SDK initialization.",
            errorSpeechNoResponse:
              "Speech recognition is taking too long. Please try again",
            errorSpeechNoWebServer:
              "For microphone access, build and run the app from a web server, not by opening the HTML file directly.",
            errorSpeechMultipleConnection:
              "Another voice recognition is ongoing. Can't start a new one.",
            errorSpeechTooMuchTimeout:
              "The voice message is too long to recognize and generate text.",
            errorSpeechUnavailable:
              "To allow voice messaging, update your browser settings to enable access to your microphone.",
            errorSpeechUnsupportedLocale:
              "The locale set for voice recognition is not supported. Please use a valid locale in 'speechLocale' setting.",
            inputPlaceholder: "Type a message",
            imageViewerClose: "Close image viewer",
            imageViewerOpen: "Open image viewer",
            itemIterator: "Item {0}",
            language_ar: "Arabic",
            language_de: "German",
            language_detect: "Detect Language",
            language_en: "English",
            language_es: "Spanish",
            language_fr: "French",
            language_hi: "Hindi",
            language_it: "Italian",
            language_nl: "Dutch",
            language_pt: "Portuguese",
            languageSelectDropdown: "Select chat language",
            linkField: "Click on the highlighted text to open Link for {0}",
            noResultText: "No more results",
            noSpeechTimeout:
              "The voice could not be detected to perform recognition.",
            noText: "No",
            oldLinkAdvisory:
              "Please note that the content of this link may have been updated since it was originally shared.",
            openMap: "Open Map",
            pin: "Close search results",
            previousChats: "End of previous conversation",
            ratingStar: "Rate {0} star",
            recognitionTextPlaceholder: "Speak your message",
            relTimeDay: "{0}d ago",
            relTimeHr: "{0}hr ago",
            relTimeMin: "{0}min ago",
            relTimeMoment: "A few seconds ago",
            relTimeMon: "{0}mth ago",
            relTimeNow: "Now",
            relTimeYr: "{0}yr ago",
            requestLocation: "Requesting location",
            requestLocationDeniedPermission:
              "To allow sharing your location, update your browser settings to enable access to your location. You can also type in the location instead.",
            requestLocationDeniedTimeout: `It is taking too long to get your location. ${wa}`,
            requestLocationDeniedUnavailable: `Your current location is unavailable. ${wa}`,
            requiredTip: "Required",
            retryMessage: "Try again",
            scrollDown: "Scroll down to read more",
            send: "Send message",
            shareAudio: "Share Audio",
            shareFailureMessage:
              "Sorry, sharing is not available on this device.",
            shareFile: "Share File",
            shareLocation: "Share Location",
            shareVisual: "Share Image/Video",
            skillMessage: "Skill says",
            showOptions: "Show Options",
            speak: "Speak a message",
            typingIndicator: "Waiting for response",
            unpin: "Pin search results",
            upload: "Share popup",
            uploadFailed: "Upload Failed.",
            uploadFileNetworkFailure:
              "Upload not completed due to network failure.",
            uploadFileSizeLimitExceeded:
              "File size should not be more than {0}MB.",
            uploadFileSizeZeroByte:
              "Files of size zero bytes can't be uploaded.",
            uploadUnauthorized: "Upload request is unauthorized.",
            uploadUnsupportedFileType: "Unsupported file type.",
            userMessage: "I say",
            utteranceGeneric: "Message from skill.",
            webViewAccessibilityTitle: "In-widget WebView to display links",
            webViewClose: "Done",
            webViewErrorInfoDismiss: "Dismiss",
            webViewErrorInfoText:
              "Don't see the page? {0}Click here{/0} to open it in a browser.",
            yesText: "Yes",
          },
          ar: { language_ar: "اَلْعَرَبِيَّةُ" },
          de: { language_de: "Deutsch" },
          es: { language_es: "Español" },
          fr: { language_fr: "Français" },
          hi: { language_hi: "हिन्दी" },
          it: { language_it: "Italiano" },
          nl: { language_nl: "Nederlands" },
          pt: { language_pt: "Português" },
        },
        initBotAudioMuted: !0,
        initMessageOptions: { sendAt: "expand" },
        disableInlineCSS: !1,
        isDebugMode: !1,
        locale: "en",
        messageCacheSizeLimit: 2e3,
        name: "oda-chat",
        openChatOnLoad: !1,
        openLinksInNewWindow: !1,
        reconnectInterval: 5,
        reconnectMaxAttempts: 5,
        shareMenuItems: [fr, wr, vr, xr],
        showConnectionStatus: !1,
        showPrevConvStatus: !0,
        showTypingIndicator: !0,
        speechLocale: we.EN_US,
        theme: br.DEFAULT,
        timestampMode: "default",
        timestampHeaderMode: "absolute",
        defaultGreetingTimeout: 5,
        defaultWaitMessageInterval: 5,
        typingIndicatorTimeout: 30,
        typingStatusInterval: 3,
        typingDelay: 0,
        upgradeToWebSocketInterval: 300,
        webViewConfig: {},
        width: "375px",
        actionsLayout: "vertical",
        globalActionsLayout: "vertical",
        cardActionsLayout: "vertical",
        formActionsLayout: "vertical",
        wcfsEnableEndConversationButtonToClose: !1,
      },
      xa = () => navigator.language.toLowerCase(),
      ka = () => {
        var e;
        return (
          (null === (e = navigator.languages) || void 0 === e
            ? void 0
            : e.map((e) => e.toLowerCase())) || []
        );
      },
      ya = (e) => za(e),
      za = (e) => {
        let t;
        try {
          t = window[e];
          const s = "__storage_test__";
          return t.setItem(s, s), t.removeItem(s), !0;
        } catch (e) {
          return (
            e instanceof DOMException &&
            (22 === e.code ||
              1014 === e.code ||
              "QuotaExceededError" === e.name ||
              "NS_ERROR_DOM_QUOTA_REACHED" === e.name) &&
            t &&
            0 !== t.length
          );
        }
      },
      $a = bn(
        '<path d="M11.007 15.117A1 1 0 0 0 13 15V7l-.005-.176A3 3 0 0 0 7 7v8l.005.217A5 5 0 0 0 17 15V5h2v10a7 7 0 1 1-14 0V7a5 5 0 0 1 10 0v8l-.005.176A3 3 0 0 1 9 15V9h2v6z"/>'
      ),
      Ca = bn(
        '<path d="M4 2h10.414L20 7.586V10h-2V9h-5V4H6v16h12v-1h2v3H4zm11 3.414L16.586 7H15z"/><path d="m7.764 17 1.849-4.87h1.012L12.486 17H11.32l-.32-.998H9.204L8.882 17zm1.722-1.883h1.226l-.617-1.916zm3.278-.415v-2.573h1.045v2.553c0 .531.079.916.235 1.152.156.233.404.349.744.349.344 0 .591-.116.743-.349.157-.236.235-.62.235-1.152v-2.553h1.045v2.573c0 .822-.165 1.427-.496 1.816-.326.384-.835.576-1.527.576s-1.204-.192-1.535-.576c-.326-.389-.489-.994-.489-1.816zM17.686 17v-4.87h1.635c.795 0 1.396.205 1.802.616.407.41.61 1.018.61 1.822 0 .795-.203 1.4-.61 1.816-.402.41-1.002.616-1.802.616zm1.622-4.02h-.577v3.17h.577c.45 0 .786-.128 1.005-.383.223-.259.335-.659.335-1.2s-.11-.94-.329-1.198c-.218-.26-.556-.389-1.011-.389z"/>'
      ),
      Sa = bn('<path fill="#161513" d="m6 9 5.975 6L18 9H6z"/>'),
      Ia = bn('<path d="M6.35 8L5 9.739 12 16l7-6.261L17.65 8 12 13.054z"/>'),
      Ma = bn('<path d="M8 17.65L9.739 19 16 12 9.739 5 8 6.35 13.054 12z"/>'),
      Ta = bn(
        '<path d="M16 17.65L14.261 19 8 12l6.261-7L16 6.35 10.946 12z"/>'
      ),
      Aa = bn(
        '<path d="M6 11h8v2H6zm0-4h12v2H6z"/><path d="M2 2v20h3.5l3-4H14v-2H7.5l-3 4H4V4h16v6h2V2z"/><path d="M20.3 12.3L19 13.6l-1.3-1.3-1.4 1.4 1.3 1.3-1.3 1.3 1.4 1.4 1.3-1.3 1.3 1.3 1.4-1.4-1.3-1.3 1.3-1.3z"/>'
      ),
      _a = bn(
        '<path d="M17.524 5 19 6.476 13.475 12 19 17.524 17.524 19 12 13.475 6.476 19 5 17.524 10.525 12 5 6.476 6.476 5 12 10.525z"/>'
      ),
      Ea = bn(
        '<path d="M11 13v9H9v-5.586l-6.293 6.293-1.414-1.414L7.586 15H2v-2zM21.293 1.293l1.414 1.414L16.414 9H22v2h-9V2h2v5.586z"/>'
      ),
      Oa = bn(
        '<path d="M4 15v5h16v-5h2v7H2v-7zm9-13v10.587l3.293-3.294 1.414 1.414L12 16.414l-5.707-5.707 1.414-1.414L11 12.585V2z"/>'
      ),
      Pa = bn(
        '<path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zM8.707 7.293l8 8-1.414 1.414-8-8z"/></svg>'
      ),
      La =
        '<svg xmlns="http://www.w3.org/2000/svg" height="20" width="20" viewBox="0 0 20 20"><path d="M4.99935 9.99967C4.99935 10.9201 4.25316 11.6663 3.33268 11.6663C2.41221 11.6663 1.66602 10.9201 1.66602 9.99967C1.66602 9.0792 2.41221 8.33301 3.33268 8.33301C4.25316 8.33301 4.99935 9.0792 4.99935 9.99967Z" fill="#161513"/><path d="M11.666 9.99967C11.666 10.9201 10.9198 11.6663 9.99935 11.6663C9.07887 11.6663 8.33268 10.9201 8.33268 9.99967C8.33268 9.0792 9.07887 8.33301 9.99935 8.33301C10.9198 8.33301 11.666 9.0792 11.666 9.99967Z" fill="#161513"/><path d="M18.3327 9.99967C18.3327 10.9201 17.5865 11.6663 16.666 11.6663C15.7455 11.6663 14.9993 10.9201 14.9993 9.99967C14.9993 9.0792 15.7455 8.33301 16.666 8.33301C17.5865 8.33301 18.3327 9.0792 18.3327 9.99967Z" fill="#161513"/></svg',
      ja =
        '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M6 9L11.9746 15L18 9H6Z" fill="#161513"/></svg>',
      Fa = bn(
        '<path class="st0" d="M20 20H4V4h7V2H2v20h20v-9h-2z"/><path xmlns="http://www.w3.org/2000/svg" class="st0" d="M14 2v2h4.6L8.3 14.3l1.4 1.4L20 5.4V10h2V2z"/>'
      ),
      Ra = bn(
        '<path d="M14.414 2 21 8.584V22H3V2.009zM13 3.999l-8 .007v15.995h14V9.996l-6 .001zm4.585 3.998L15 5.413v2.585z"/>'
      ),
      Na = bn(
        '<path d="M4 2h10.414L20 7.586V22H4zm2 2v16h12V9h-5V4zm9 1.414L16.586 7H15z"/><path d="M16 12a1 1 0 11-2 0 1 1 0 012 0zm-6.143 1L7 19h10l-2.857-4.5L12 16.75z"/>'
      ),
      Da = bn(
        '<path d="M22 5v14H2V5zm-2 2H4v10h16zM7 13v2H5v-2zm12 0v2h-2v-2zm-4 0v2H9v-2zM7 9v2H5V9zm12 0v2h-2V9zm-4 0v2h-2V9zm-4 0v2H9V9z" />'
      ),
      Ha = bn(
        '<path d="M13 14c-1.5 0-2.9-.4-4-1.1 1.1-2.4 1.7-5 1.9-6.9h9V4H7V2H5v2H2v2h6.9c-.2 1.7-.7 3.7-1.5 5.6C6.5 10.5 6 9.2 6 8H4c0 1.9.9 4 2.5 5.5C5.3 15.5 3.8 17 2 17v2c2.6 0 4.6-1.9 6.1-4.3 1.4.8 3 1.3 4.9 1.3zm7.6 4.6L17 10.5l-3.6 8.1-1.3 3 1.8.8L15 20h4l1.1 2.4 1.8-.8zm-4.7-.6l1.1-2.5 1.1 2.5z"/>'
      ),
      Ua =
        '<svg width="36" height="36" viewBox="0 0 36 36"><path fill-rule="evenodd" clip-rule="evenodd" d="M7.875 8.625a2.25 2.25 0 00-2.25 2.25v16c0 .621.504 1.125 1.125 1.125h.284c.298 0 .585-.119.796-.33l2.761-2.76a2.25 2.25 0 011.59-.66h15.944a2.25 2.25 0 002.25-2.25V10.875a2.25 2.25 0 00-2.25-2.25H7.875zM24.75 18a2.25 2.25 0 100-4.5 2.25 2.25 0 000 4.5zm-4.5-2.25a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-9 2.25a2.25 2.25 0 100-4.5 2.25 2.25 0 000 4.5z" fill="#fff"/></svg>',
      Va = bn(
        '<path d="M4.014 3C2.911 3 2 3.888 2 4.992v15c0 .6.408 1.008 1.007 1.008h.6a.887.887 0 0 0 .695-.288l3.094-3.12c.407-.384.91-.6 1.415-.6h11.175C21.089 16.992 22 16.104 22 15V4.992C22 3.888 21.089 3 19.986 3zm3.981 7.008A1.986 1.986 0 0 1 6.005 12c-1.103 0-1.99-.888-1.99-1.992s.887-2.016 1.99-2.016 1.99.912 1.99 2.016zm5.995 0C13.99 11.112 13.103 12 12 12s-1.99-.888-1.99-1.992.887-2.016 1.99-2.016 1.99.912 1.99 2.016zm5.996 0c0 1.104-.888 1.992-1.99 1.992s-1.991-.888-1.991-1.992.887-2.016 1.99-2.016 1.99.912 1.99 2.016z" fill="#fff"/>'
      ),
      Ba = bn(
        '<path d="M7 22v-2h4v-2.062C7.06 17.444 4 14.073 4 10h2c0 3.309 2.691 6 6 6s6-2.691 6-6h2c0 4.072-3.059 7.444-7 7.938V20h4v2h-6zm5-20c2.206 0 4 1.794 4 4v4c0 2.206-1.794 4-4 4s-4-1.794-4-4V6c0-2.206 1.794-4 4-4zm0 2c-1.103 0-2 .897-2 2v4c0 1.103.897 2 2 2s2-.897 2-2V6c0-1.103-.897-2-2-2z"/>'
      ),
      Wa = bn(
        '<path d="M19.33 23.02l-7.332-3.666-7.332 3.666 1.418-7.995L1 9.555l7.331-1.222L11.998 1l3.666 7.333 7.332 1.222-5.084 5.47z"/>'
      ),
      qa = bn(
        '<path d="M10 2a8 8 0 016.317 12.91l5.383 5.384-1.414 1.414-5.386-5.384A8 8 0 1110 2zm0 2a6 6 0 100 12 6 6 0 000-12z" fill="rgb(22, 21, 19)"/>'
      ),
      Za = bn(
        '<path d="M13 22V5.414l5.293 5.293 1.414-1.414L12 1.585 4.293 9.293l1.414 1.414L11 5.414V22h2z" fill="#161513"/>'
      ),
      Ga = bn(
        '<path d="M22 2v20H2V2zm-2 2H4v16h16zm-3 1.674V14a2 2 0 11-2.15-1.995L15 12V8.326l-5 1.428V16a2 2 0 11-2.15-1.995L8 14V8.246z"/>'
      ),
      Ya = bn(
        '<path d="M13.414 2L17 5.586V7h.414L21 10.586V22H7v-4H3V2zM17 9.414V18H9v2h10v-8.586zm-2-3L12.586 4H5v12h10zM13 11v2H7v-2zm-2-4v2H7V7z"/>'
      ),
      Ja = bn(
        '<path d="M12 2c3.874 0 6.994 3.28 6.99 7.214l.011.285c.008.927-.202 2.23-.787 3.837-.96 2.639-2.73 5.452-5.49 8.353L12 22.45l-.724-.761c-2.76-2.901-4.53-5.714-5.49-8.353-.627-1.722-.823-3.095-.782-4.03l.006-.252C5.134 5.147 8.205 2 12 2zm0 2C9.254 4 7.006 6.362 7.002 9.386L7 9.529c-.004.694.168 1.753.667 3.123.741 2.036 2.038 4.221 4.014 6.507l.32.365.32-.365c1.867-2.159 3.127-4.228 3.886-6.166l.128-.34c.535-1.469.694-2.58.664-3.259l-.008-.32C16.879 6.244 14.676 4 12 4zm0 2a3 3 0 1 1-.001 6A3 3 0 0 1 12 6zm0 2a1 1 0 1 0 .001 2A1 1 0 0 0 12 8z"/>'
      ),
      Ka = bn(
        '<path d="M22 2v16h-4v4H2V6h4V2zm-9.036 12.378L6.93 20H16v-2.585zM16 8H4v11.999l9.036-8.377L16 14.585zm4-4H8v2h10v10h2zM7 9a2 2 0 110 4 2 2 0 010-4z"/>'
      ),
      Xa = bn(
        '<path fill="#161513" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12zm15.207-2.793-1.414-1.414L10 13.586l-2.293-2.293-1.414 1.414L10 16.414z"/>'
      ),
      Qa = bn(
        '<path d="M1.707.293l22 22-1.414 1.414L12 13.414V21l-6.35-5.114H1V7.954h4.65l.5-.39L.293 1.707zM19.67 4.446c2.119 1.967 3.302 4.613 3.33 7.452a10.363 10.363 0 01-1.392 5.295l-1.476-1.476c.58-1.18.88-2.472.868-3.8-.023-2.29-.981-4.43-2.697-6.025zM7.583 8.996l-1.232.955H3v3.964h3.351L10 16.875v-5.461zm8.051-1.68C17.15 8.547 17.991 10.21 18 11.999c.003.482-.055.956-.17 1.416l-1.86-1.86c-.133-1.017-.691-1.964-1.604-2.706zM12 3v4.586L9.424 5.01z"/>'
      ),
      en = bn(
        '<path d="M13 3v18l-6.35-5.114H2V7.954h4.65zm5.67 1.446c2.119 1.967 3.302 4.613 3.33 7.452.029 2.904-1.15 5.658-3.316 7.75l-1.396-1.421c1.772-1.71 2.735-3.95 2.712-6.31-.023-2.29-.981-4.43-2.697-6.025zM11 7.125L7.351 9.95H4v3.964h3.351L11 16.875zm4.634.19C17.15 8.548 17.991 10.212 18 12c.01 1.806-.828 3.5-2.358 4.771l-1.284-1.519c1.065-.885 1.65-2.037 1.642-3.242-.006-1.187-.587-2.309-1.634-3.16z"/>'
      ),
      tn = bn(
        '<path d="M4 2h10.414L20 7.586V10h-2V9h-5V4H6v16h12v-1h2v3H4zm11 3.414L16.586 7H15z"/><path d="m12.36 17-1.796-4.87h1.18l1.138 3.584 1.153-3.585h1.132L13.37 17zm3.33 0v-4.87h1.046V17zm1.996 0v-4.87h1.635c.795 0 1.396.205 1.802.616.407.41.61 1.018.61 1.822 0 .795-.203 1.4-.61 1.816-.402.41-1.002.616-1.802.616zm1.622-4.02h-.577v3.17h.577c.45 0 .786-.128 1.005-.383.223-.259.335-.659.335-1.2s-.11-.94-.329-1.198c-.218-.26-.556-.389-1.011-.389z"/>'
      ),
      sn = bn(
        '<path fill="#161513" d="m12 2 10 18H2zm-1 12h2v-4h-2zm0 1v2h2v-2z"/>'
      ),
      on = bn(
        '<path d="M11 2a9 9 0 017.032 14.617l3.675 3.676-1.414 1.414-3.676-3.675A9 9 0 1111 2zm0 2a7 7 0 100 14 7 7 0 000-14zm1 3v3h3v2h-3v3h-2v-3H7v-2h3V7z"/>'
      ),
      rn = bn(
        '<path fill="#161513" fill-rule="evenodd" d="M21.205 6.707 8.998 18.914l-6.707-6.707 1.414-1.414 5.293 5.293L19.791 5.293l1.414 1.414Z" clip-rule="evenodd"/>'
      ),
      an = bn(
        '<path fill="#161513" d="M10.998 3c0-.55.45-1 1-1s1 .44 1 1c0 .55-.44 1-.99 1a.999.999 0 0 1-1.01-1Zm0 18c0-.55.45-1 1-1s1 .44 1 1c0 .55-.44 1-.99 1a.999.999 0 0 1-1.01-1Zm11-9c0-.55-.45-1-1-1-.56 0-1 .45-1 1.01 0 .55.45.99 1 .99.56 0 1-.45 1-1Zm-19-1c.55 0 1 .45 1 1s-.44 1-1 1c-.55 0-1-.44-1-.99 0-.56.44-1.01 1-1.01Zm1.93-6.072a1.004 1.004 0 0 0 0 1.415.998.998 0 0 0 1.42-.007.995.995 0 0 0-.007-1.408.997.997 0 0 0-1.414 0Zm12.727 14.143a1.004 1.004 0 0 1 0-1.415.997.997 0 0 1 1.414 0 .995.995 0 0 1 .007 1.408.998.998 0 0 1-1.421.007ZM6.34 17.657a1.003 1.003 0 0 0-1.414 0 .998.998 0 0 0 .007 1.42.994.994 0 0 0 1.407-.005.997.997 0 0 0 0-1.415ZM3.336 9.359a1.004 1.004 0 0 1-.523-1.314.997.997 0 0 1 1.314-.523.995.995 0 0 1 .527 1.305 1 1 0 0 1-1.318.532Zm16.01 5.806a1 1 0 1 0 1.841.782.994.994 0 0 0-.527-1.305.997.997 0 0 0-1.314.523ZM7.52 19.87a1.003 1.003 0 0 1 1.314-.523.996.996 0 0 1 .523 1.314.995.995 0 0 1-1.305.527 1 1 0 0 1-.532-1.318Zm-4.18-5.23a.995.995 0 0 0-.527 1.305 1 1 0 1 0 .527-1.305Zm5.488-9.984a.995.995 0 0 1-1.305-.527.997.997 0 0 1 .523-1.314.999.999 0 1 1 .782 1.841Zm5.814 16.005c.218.505.8.744 1.305.527a.999.999 0 1 0-.782-1.841.997.997 0 0 0-.523 1.314Z"/>'
      ),
      nn = bn(
        '<path fill="#161513" d="M3.47 1.667h14.862v9.166h-4.459l-3.333 7.5h-.542c-1.157 0-2.002-.324-2.566-.846-.551-.511-.767-1.152-.767-1.654V12.5H1.5L3.47 1.667Zm10.695 7.5h2.5V3.333h-2.5v5.834Zm-1.667-5.834H4.86l-1.363 7.5h4.835v5c0 .055.034.247.232.43.143.132.412.298.908.369l3.026-6.809v-6.49Z"/>',
        "20"
      ),
      cn = bn(
        '<path fill="#161513" d="M3.47 18.333h14.862V9.167h-4.459l-3.333-7.5h-.542c-1.157 0-2.002.324-2.566.847-.551.51-.767 1.151-.767 1.653V7.5H1.5l1.97 10.833Zm10.695-7.5h2.5v5.834h-2.5v-5.834Zm-1.667 5.834H4.86l-1.363-7.5h4.835v-5c0-.055.034-.247.232-.43.143-.132.412-.298.908-.369l3.026 6.809v6.49Z"/>',
        "20"
      ),
      hn = bn(
        '<path fill="#C74634" d="M3.345 2.5c-.92 0-1.679.74-1.679 1.66v12.5c0 .5.34.84.84.84h.499c.26 0 .42-.08.58-.24l2.577-2.6c.34-.32.76-.5 1.18-.5h9.312c.92 0 1.679-.74 1.679-1.66V4.16c0-.92-.76-1.66-1.679-1.66H3.344Zm3.317 5.84c0 .92-.74 1.66-1.659 1.66s-1.658-.74-1.658-1.66c0-.92.74-1.68 1.658-1.68.92 0 1.659.76 1.659 1.68Zm4.996 0c0 .92-.74 1.66-1.659 1.66s-1.658-.74-1.658-1.66c0-.92.74-1.68 1.658-1.68.92 0 1.659.76 1.659 1.68Zm4.996 0c0 .92-.74 1.66-1.659 1.66s-1.658-.74-1.658-1.66c0-.92.74-1.68 1.658-1.68.92 0 1.659.76 1.659 1.68Z"/>',
        "20"
      ),
      ln = bn(
        '<path fill="#C74634" d="M2.677 2c-.736 0-1.343.592-1.343 1.328v10c0 .4.272.672.671.672h.4a.591.591 0 0 0 .464-.192l2.062-2.08c.272-.256.608-.4.943-.4h7.45c.736 0 1.343-.592 1.343-1.328V3.328c0-.736-.607-1.328-1.343-1.328H2.677ZM5.33 6.672C5.33 7.408 4.739 8 4.004 8a1.324 1.324 0 0 1-1.327-1.328c0-.736.591-1.344 1.327-1.344.735 0 1.327.608 1.327 1.344Zm3.997 0C9.328 7.408 8.736 8 8 8a1.324 1.324 0 0 1-1.327-1.328c0-.736.591-1.344 1.327-1.344.735 0 1.327.608 1.327 1.344Zm3.996 0c0 .736-.591 1.328-1.326 1.328a1.324 1.324 0 0 1-1.327-1.328c0-.736.591-1.344 1.327-1.344.735 0 1.326.608 1.326 1.344Z"/>',
        "16"
      ),
      pn = bn(
        '<path fill="#8F520A" d="M1.332 14.667 7.998 1.333l6.667 13.334H1.332Zm6-7.334V10h1.333V7.333H7.332Zm0 4v1.334h1.333v-1.334H7.332Z"/>',
        "16"
      ),
      dn = bn(
        '<path fill="#211e1c" fill-rule="evenodd" d="M10.364 4c4.665 0 8.492 3.29 8.632 7.747L19 12v1.585l1.293-1.292 1.414 1.414L18 17.414l-3.707-3.707 1.414-1.414L17 13.585V12c0-3.419-2.935-6-6.636-6C6.853 6 4 8.906 4 12.5S6.853 19 10.364 19a6.243 6.243 0 0 0 3.764-1.258l.228-.18 1.272 1.544A8.25 8.25 0 0 1 10.364 21C5.74 21 2 17.19 2 12.5 2 7.81 5.74 4 10.364 4z"/>'
      ),
      un = bn('<path d="M3 3h18v18H3zm2 2v14h14V5z"/>'),
      gn = bn(
        '<path d="M11 1.994v16.585l-5.293-5.293-1.414 1.415L12 22.408l7.707-7.707-1.414-1.414L13 18.578V1.994z"/>'
      ),
      mn = bn(
        '<path d="M13.5 1.1l-3.1 3.2.6 2.1-2.8 2.7H4.1l-2.3 2.4 4.1 4.1-4.1 4.1 1.4 1.4L7.3 17l4.1 4.1 2.4-2.4v-4l2.8-2.8 2.1.7 3.2-3.2zm4.5 9.2l-2-.7-4.2 4.3v4l-.4.4-6.8-6.8.4-.4h4l4.2-4.2-.7-2.1 1-.8L19 9.5z" fill="#161513"/>'
      );
    function bn(e, t) {
      return `<svg xmlns="http://www.w3.org/2000/svg" height="20" width="20" viewBox="0 0 ${
        t || "24"
      } ${t || "24"}">${e}</svg>`;
    }
    const fn = "";
    function wn(e, t) {
      if (!t) return Promise.resolve(!1);
      if ((Array.isArray(t) || (t = [t]), !t.length))
        return Promise.resolve(!1);
      const s = t.map((e) => {
        var t;
        return null === (t = e.lang) || void 0 === t ? void 0 : t.toLowerCase();
      });
      return e.getVoices().then((e) => {
        let t = !1;
        const i = e.map((e) => e.lang.toLowerCase());
        for (const e of s)
          if (i.includes(e)) {
            t = !0;
            break;
          }
        return t;
      });
    }
    function vn(e, t, s, i) {
      return pr.fromMessage(
        s,
        e,
        { messagePayload: { type: Oe.Form, forms: [t] } },
        i
      );
    }
    const xn = (e) =>
        "number" == typeof e && isFinite(e) && Math.floor(e) === e,
      kn = (e) => {
        const t = e.match(/<svg\s/gi);
        return t && t.length > 0;
      },
      yn = /<br\s*\/?>/g,
      zn = (e) => e.replace(yn, "\n");
    const $n = [
      { match: /<([a-z])/gi, replace: (e, t) => `&#x3c;${t}` },
      { match: /<\/([a-z])/gi, replace: (e, t) => `&#x3c;&#47;${t}` },
    ];
    function Cn(e, t) {
      for (let s = 0; s < e.childElementCount; s++) {
        const i = e.children[s];
        if ("a" === i.tagName.toLowerCase()) {
          const e = i;
          (e.rel = "noreferrer noopener"),
            t.onclick && (e.onclick = t.onclick.bind(e)),
            t.target && (e.target = t.target);
        }
        i.hasChildNodes() && Cn(i, t);
      }
    }
    function Sn(e) {
      for (let t = 0; t < e.childElementCount; t++) {
        const s = e.children[t];
        "a" === s.tagName.toLowerCase() &&
          (s.onclick = (e) => (
            window.open(
              s.href,
              fn,
              "height=450px,width=800px,menubar,toolbar,personalbar,status,resizable,noopener,noreferrer"
            ),
            e.preventDefault(),
            e.stopPropagation(),
            !1
          )),
          s.hasChildNodes() && Sn(s);
      }
    }
    const In = (() => {
      let e = !1;
      return (
        t = {
          hasRecognition: !1,
          hasSynthesis: !1,
          isReset: !1,
          recognitionLocale: fn,
          synthesisLocales: [],
        }
      ) => {
        var s;
        t.isReset && (e = !1);
        let i = t.synthesisLocales;
        return (
          Array.isArray(i) || (i = []),
          t.hasRecognition &&
            t.hasSynthesis &&
            (null === (s = t.recognitionLocale) || void 0 === s
              ? void 0
              : s.length) &&
            ((!e && t.synthesisLocales.length) ||
              ((e = !0), (i = [{ lang: t.recognitionLocale }]))),
          i
        );
      };
    })();
    function Mn(e, t) {
      const s = e.toLowerCase();
      for (const e in t) if (s === e.toLowerCase()) return !0;
      return !1;
    }
    function Tn(e, t) {
      const s = e.toLowerCase().split("-")[0];
      for (const e in t) if (s === e.toLowerCase()) return !0;
      return !1;
    }
    function An(e, t) {
      let s;
      return function () {
        const i = this,
          o = arguments;
        clearTimeout(s),
          (s = setTimeout(function () {
            (s = null), e.apply(i, o);
          }, t));
      };
    }
    function _n(e, t) {
      let s = !1;
      return function () {
        const i = this;
        s ||
          (e.apply(i, arguments),
          (s = !0),
          setTimeout(() => {
            s = !1;
          }, t));
      };
    }
    function En(e, t = !1) {
      let s = e.title ? `${e.title} - ` : fn;
      return (
        Ge(e)
          ? e.fields.forEach((e) => {
              s += On(e);
            })
          : e.formRows.forEach((e) => {
              e.columns.forEach((e) => {
                e.fields.forEach((e) => {
                  It(e) && (s += On(e));
                });
              });
            }),
        t ? Rn(s) : s
      );
    }
    function On(e) {
      const t = e.value || e.label;
      return t ? `${t} - ` : fn;
    }
    function Pn(e) {
      const t = {};
      return (
        e &&
          Object.keys(e).forEach((s) => {
            var i;
            t[s] =
              null === (i = document.getElementById(e[s])) || void 0 === i
                ? void 0
                : i.value;
          }),
        t
      );
    }
    const Ln = {
      avatarAgent: "agentAvatar",
      avatarBot: "botIcon",
      avatarUser: "personIcon",
      fileAudio: "audioIcon",
      fileImage: "imageIcon",
      fileGeneric: "fileIcon",
      fileVideo: "videoIcon",
      clearHistory: "clearMessageIcon",
      close: void 0,
      collapse: "closeIcon",
      download: "downloadIcon",
      error: "errorIcon",
      expandImage: "expandImageIcon",
      keyboard: "keyboardIcon",
      logo: "logoIcon",
      launch: "botButtonIcon",
      mic: "micIcon",
      rating: void 0,
      send: "sendIcon",
      shareMenu: "attachmentIcon",
      shareMenuAudio: void 0,
      shareMenuFile: void 0,
      shareMenuLocation: void 0,
      shareMenuVisual: void 0,
      ttsOff: "audioResponseOffIcon",
      ttsOn: "audioResponseOnIcon",
      typingIndicator: "chatBubbleIcon",
    };
    function jn(e) {
      const t = {},
        s = Object.keys(e);
      for (const i of s) t[i.toLowerCase()] = e[i];
      return t;
    }
    function Fn(e) {
      const t = Object.assign(Object.assign({}, va), e);
      if (
        (e.i18n &&
          Object.keys(e.i18n).length &&
          (t.i18n = (function (e, t) {
            (e = jn(e)), (t = jn(t));
            const s = new Set();
            Object.keys(e).forEach((e) => {
              s.add(e);
            }),
              Object.keys(t).forEach((e) => {
                s.add(e);
              });
            const i = {};
            return (
              s.forEach((s) => {
                i[s] = Object.assign(
                  Object.assign(Object.assign({}, e.en), e[s]),
                  t[s]
                );
              }),
              i
            );
          })(va.i18n, e.i18n)),
        (t.colors = Object.assign(Object.assign({}, va.colors), e.colors)),
        (t.userId = e.userId || ae({ prefix: "user" })),
        (t.icons = (function (e) {
          const t = e.icons || {};
          for (const s in Ln) {
            const i = s,
              o = Ln[i];
            o in e && (t[i] = e[o]);
          }
          return t;
        })(t)),
        (t.locale = (function (e, t) {
          let s = [e.toLowerCase()],
            i = "en";
          (s = s.concat(ka())), s.includes(i) || s.push(i);
          for (const e of s) {
            if (Mn(e, t)) {
              i = e;
              break;
            }
            if (Tn(e, t)) {
              i = e.split("-")[0];
              break;
            }
          }
          return i;
        })(t.locale, t.i18n)),
        e.typingStatusInterval &&
          e.typingStatusInterval < va.typingStatusInterval &&
          (t.typingStatusInterval = va.typingStatusInterval),
        t.enableVoiceOnlyMode &&
          ((t.enableBotAudioResponse = !0),
          (t.initBotAudioMuted = !1),
          (t.enableSpeech = !0)),
        !t.position)
      ) {
        const e = "rtl" === window.getComputedStyle(document.body).direction;
        t.position = e
          ? { left: "20px", bottom: "20px" }
          : { right: "20px", bottom: "20px" };
      }
      return t;
    }
    function Rn(e) {
      return e.length ? e.slice(0, e.length - 3) : e;
    }
    function Nn(e, t) {
      for (const [s, i] of Object.entries(t)) e.setAttribute(s, i);
    }
    const Dn = (e) =>
        e.type === $e.Client && e.actionType === Le.COPY_MESSAGE_TEXT,
      Hn = (e, t) => {
        e.querySelectorAll("a").forEach((e) => {
          e.title = t;
        });
      },
      Un = "aria-expanded",
      Vn = "aria-activedescendant",
      Bn = "expand",
      Wn = !0;
    class qn {
      get cssPrefix() {
        return this.Xi;
      }
      constructor(e) {
        (this.Bp = {}), (this.Wp = []), (this.Xi = e.name);
      }
      addCSSClass(e, ...t) {
        e.classList
          ? t.forEach((t) => e.classList.add(`${this.Xi}-${t}`))
          : e.setAttribute(
              "class",
              t.reduce((e, t) => `${e} ${this.Xi}-${t}`, "")
            );
      }
      createAnchor(e, t, s = [], i = !1, o) {
        const r = this.createElement("a", s, Wn);
        r.rel = "noreferrer noopener";
        let a = !1;
        return (
          (r.href = e),
          (r.innerText = t),
          o &&
            (o.onclick && ((r.onclick = o.onclick.bind(r)), (a = !0)),
            o.target && ((r.target = o.target), (a = !0))),
          a ||
            (i
              ? r.addEventListener(
                  "click",
                  (t) => (
                    window.open(
                      e,
                      "",
                      "height=450px,width=800px,menubar,toolbar,personalbar,status,resizable,noopener,noreferrer"
                    ),
                    t.preventDefault(),
                    t.stopPropagation(),
                    !1
                  )
                )
              : (r.target = "_blank")),
          r
        );
      }
      createButton(e = []) {
        const t = "button",
          s = this.createElement(t, ["widget-button", ...e, "flex"], Wn);
        return (s.type = t), s;
      }
      createDiv(e = []) {
        return this.createElement("div", e);
      }
      createElement(e, t = [], s = !1) {
        const i = document.createElement(e);
        return this.qp(i, t), s && (i.dir = "auto"), i;
      }
      createElementFromString(e, t = []) {
        const s = this.createDiv();
        s.innerHTML = e.trim();
        const i = s.firstElementChild;
        return t && this.qp(s.firstElementChild, t), i;
      }
      createIconButton({ css: e, icon: t, title: s, iconCss: i }) {
        const o = this.createButton(["icon", ...e]);
        (o.innerHTML = ""), (o.title = s);
        const r = this.createImageIcon({ icon: t, iconCss: i });
        return o.appendChild(r), o;
      }
      createImage(e, t = [], s = "") {
        const i = this.createElement("img", t);
        return (
          e && (i.src = e), (i.alt = s), i.setAttribute("draggable", "false"), i
        );
      }
      createImageIcon({ icon: e, iconCss: t }) {
        if (kn(e)) {
          const s = this.createElementFromString(e, t);
          return (
            s.setAttribute("role", "presentation"),
            s.setAttribute("focusable", "false"),
            s
          );
        }
        return this.createImage(e, t);
      }
      createInputElement(e, t = []) {
        const s = this.createElement("input", ["input", ...t], !0);
        return this.setAttributes(s, e), s;
      }
      createLabel(e = []) {
        return this.createElement("label", ["label", ...e], Wn);
      }
      createTextDiv(e = []) {
        return this.createElement("div", e, Wn);
      }
      createTextSpan(e = []) {
        return this.createElement("span", e, Wn);
      }
      setAttributes(e, t) {
        const s = ["valueOn", "valueOff"];
        Object.keys(t).forEach((i) => {
          const o = t[i];
          o &&
            ("errorMsg" === i
              ? e.setAttribute("data-error", o)
              : s.includes(i)
              ? e.setAttribute(i, o)
              : (e[i] = o));
        });
      }
      createListItem(e, t, s, i, o, r, a = !1, n = !0) {
        const c = this.createElement("li", ["li", o, a && "with-sub-menu"], !0);
        if (
          ((c.id = e),
          (c.tabIndex = -1),
          c.setAttribute("role", "menuitem"),
          s && c.setAttribute("data-value", s),
          i)
        ) {
          const e = this.createImageIcon({
            icon: i,
            iconCss: ["icon", `${o}-icon`],
          });
          c.appendChild(e);
        }
        const h = this.createTextSpan([
          "text",
          `${o}-text`,
          n ? "ellipsis" : "",
        ]);
        return (h.innerText = t), c.appendChild(h), r && Zn(c, "click", r), c;
      }
      createMedia(e, t, s = []) {
        const i = this.createElement(e, s, !0);
        return t && (i.src = t), (i.autoplay = !1), i;
      }
      getMenu(e) {
        const t = this.createElement("ul", ["popup", ...e.menuClassList]);
        (t.id = e.menuId),
          (t.tabIndex = -1),
          t.setAttribute("role", "menu"),
          t.setAttribute("aria-labelledby", e.buttonId),
          (t.ariaHidden = "true");
        const s = e.menuItems;
        if ((s.forEach((e) => t.appendChild(e)), e.defaultValue)) {
          const s = t.querySelector(`[data-value="${e.defaultValue}"]`);
          this.addCSSClass(s, "active");
        }
        return (
          Zn(t, "click", () => this.Zp(t, e.menuButton)),
          Zn(t, "keydown", (i) => {
            let o = !1;
            if (!(i.ctrlKey || i.altKey || i.metaKey)) {
              if (i.shiftKey && i.code === U) this.Zp(e.menuButton, t);
              else
                switch (i.code) {
                  case F:
                  case N:
                    i.target.click(), (o = !0);
                    break;
                  case R:
                  case U:
                    this.Zp(e.menuButton, t),
                      i.code === R && (e.menuButton.focus(), (o = !0));
                    break;
                  case D:
                    this.Gp(t), (o = !0);
                    break;
                  case H:
                    this.Yp(t), (o = !0);
                    break;
                  case W:
                  case B:
                    this.Jp(t, s), (o = !0);
                    break;
                  case q:
                  case V:
                    this.Kp(t, s), (o = !0);
                }
              o && (i.stopPropagation(), i.preventDefault());
            }
          }),
          t
        );
      }
      getMenuButton(e) {
        const t = e.button,
          s = e.menu,
          i = s.querySelectorAll("li"),
          o = t.classList.contains(`${this.Xi}-with-sub-menu`),
          r = e.widget;
        return (
          t.setAttribute("role", "button"),
          t.setAttribute("aria-haspopup", "true"),
          t.setAttribute(Un, "false"),
          t.setAttribute("aria-controls", e.menuId),
          Zn(t, "click", () => {
            const s = document.getElementById(e.menuId);
            "true" === t.getAttribute(Un) ? this.Zp(t, s) : this.Xp(t, s, r, o);
          }),
          Zn(t, "keydown", (e) => {
            let a = !1;
            switch (e.code) {
              case F:
              case H:
              case N:
                this.Xp(t, s, r, o), this.Jp(s, i), (a = !0);
                break;
              case D:
                this.Xp(t, s, r, o), this.Kp(s, i), (a = !0);
            }
            a && (e.stopPropagation(), e.preventDefault());
          }),
          t
        );
      }
      getMessage(e, t = !1) {
        const s = "message",
          i = this.createDiv([s]),
          o = this.createDiv([`${s}-wrapper`]),
          r = this.createDiv([`${s}-bubble`, t && "error"]);
        return r.appendChild(e), o.appendChild(r), i.appendChild(o), i;
      }
      wrapMessageBlock(e, t, s = to) {
        const i = "message",
          o = this.createDiv([`${i}-block`, "flex", s]),
          r = this.createDiv([`${i}s-wrapper`]),
          a = this.createDiv([`${i}-list`, "flex", "col"]);
        if (t) {
          const e = this.createImageIcon({
              icon: t,
              iconCss: ["message-icon"],
            }),
            s = this.createDiv(["icon-wrapper"]);
          s.appendChild(e), o.appendChild(s);
        }
        return a.appendChild(e), r.appendChild(a), o.appendChild(r), o;
      }
      getMessageBlock(e, t, s, i = !1) {
        return this.wrapMessageBlock(this.getMessage(t, i), s, e);
      }
      removeCSSClass(e, ...t) {
        var s, i;
        if (e.classList)
          t.forEach((t) => e.classList.remove(`${this.Xi}-${t}`));
        else {
          const t = "class",
            o =
              null !==
                (i =
                  null === (s = e.getAttribute(t)) || void 0 === s
                    ? void 0
                    : s.split(" ")) && void 0 !== i
                ? i
                : [];
          if (o.length) {
            const s = o.filter((e) => !o.includes(`${this.Xi}-${e}`)).join(" ");
            e.setAttribute(t, s);
          }
        }
      }
      setChatWidgetWrapper(e) {
        this.Qp = e;
        for (const [e, t] of Object.entries(this.Bp)) this.updateCSSVar(e, t);
      }
      updateCSSVar(e, t) {
        (this.Bp[e] = t), this.Qp && this.Qp.style.setProperty(e, t);
      }
      qp(e, t = []) {
        return t && this.addCSSClass(e, ...t), e;
      }
      Zp(e, t) {
        e.getAttribute(Un) &&
          (this.removeCSSClass(t, Bn),
          (t.ariaHidden = "true"),
          e.setAttribute(Un, "false"));
      }
      Jp(e, t) {
        this.ed(t[0], e);
      }
      Kp(e, t) {
        this.ed(t[t.length - 1], e);
      }
      Gp(e) {
        const t = e.getAttribute(Vn),
          s = e.querySelector(`#${t}`);
        this.ed(s.previousSibling || e.lastChild, e);
      }
      Yp(e) {
        const t = e.getAttribute(Vn),
          s = e.querySelector(`#${t}`);
        this.ed(s.nextSibling || e.firstChild, e);
      }
      ed(e, t) {
        e.focus(), t.setAttribute(Vn, e.id);
      }
      Xp(e, t, s, i = !1) {
        if ("false" === e.getAttribute(Un)) {
          this.addCSSClass(t, Bn), e.setAttribute(Un, "true");
          const o = s.getBoundingClientRect(),
            r = e.getBoundingClientRect(),
            a = "rtl" === window.getComputedStyle(t).direction;
          if (i) {
            const i = 48;
            (t.style.top = `${e.offsetTop + e.offsetHeight + 60}px`),
              a ? (t.style.left = `${i}px`) : (t.style.right = `${i}px`),
              (t.style.maxWidth = s.offsetWidth - i + "px");
          } else {
            let e = o.right - r.right;
            a
              ? ((e = r.left - o.left), (t.style.left = `${e}px`))
              : (t.style.right = `${e}px`),
              (t.style.maxWidth = s.offsetWidth - e + "px");
          }
          setTimeout(() => {
            t.ariaHidden = "false";
            const s = document.querySelectorAll(`.${this.Xi}-with-sub-menu`);
            document.addEventListener(
              "click",
              (i) => {
                let o = !1;
                s.forEach((e) => {
                  e.contains(i.target) && (o = !0);
                }),
                  o
                    ? this.Wp.push({ menu: t, menuButton: e })
                    : (this.Wp.length &&
                        (this.Wp.forEach((e) => {
                          this.Zp(e.menuButton, e.menu);
                        }),
                        (this.Wp = [])),
                      this.Zp(e, t));
              },
              { once: !0 }
            );
          }, 400);
        }
      }
    }
    function Zn(e, t, s, i) {
      e.addEventListener(t, s, i);
    }
    function Gn(e, t, s, i) {
      e.removeEventListener(t, s, i);
    }
    const Yn = 100;
    class Jn {
      constructor(e, t, s) {
        (this.gp = e),
          (this.handle = t),
          (this.moveElement = s),
          (this.active = !1),
          (this.dragged = !1),
          (this.currentX = 0),
          (this.currentY = 0),
          (this.initialX = 0),
          (this.initialY = 0),
          (this.pointerEventsDefault = null),
          (this.dragBound = this.drag.bind(this)),
          (this.dragEndBound = this.dragEnd.bind(this));
      }
      makeElementDraggable() {
        void 0 === this.moveElement && (this.moveElement = this.handle),
          (this.handle.style.userSelect = "none");
        const e = An(() => {
          document.body.contains(this.moveElement)
            ? (this.moveBackInScreen(0, 0),
              (this.moveElement.style.transform = `translate(${this.currentX}px, ${this.currentY}px)`))
            : window.removeEventListener("resize", e);
        }, 500);
        window.addEventListener("resize", e),
          this.handle.addEventListener("touchstart", this.dragStart.bind(this)),
          this.handle.addEventListener("mousedown", this.dragStart.bind(this));
      }
      moveBackInScreen(e, t) {
        const s = this.handle.getBoundingClientRect(),
          i = s.width > Yn ? s.width : Yn,
          o = s.height > Yn ? s.height : Yn;
        s.left - e + (i - Yn) < 0 &&
          (this.currentX = this.currentX - (s.left - e) - (i - Yn)),
          s.right - e - (i - Yn) > document.body.clientWidth &&
            (this.currentX =
              this.currentX -
              (s.right - document.body.clientWidth) +
              e +
              (i - Yn)),
          s.top - t + (o - Yn) < 0 &&
            (this.currentY = this.currentY - (s.top - t) - (o - Yn)),
          s.bottom - t - (o - Yn) > window.innerHeight &&
            (this.currentY =
              this.currentY - (s.bottom - window.innerHeight) + t + (o - Yn));
      }
      dragStart(e) {
        let t, s;
        "touchstart" === e.type
          ? ((t = e.touches[0].clientX), (s = e.touches[0].clientY))
          : ((t = e.clientX), (s = e.clientY)),
          (this.initialX = t - this.currentX),
          (this.initialY = s - this.currentY),
          (this.active = !0),
          document.addEventListener("touchmove", this.dragBound),
          document.addEventListener("mousemove", this.dragBound),
          document.addEventListener("touchend", this.dragEndBound),
          document.addEventListener("mouseup", this.dragEndBound);
      }
      drag(e) {
        let t, s;
        if (this.active) {
          "touchmove" === e.type
            ? ((t = e.touches[0].clientX), (s = e.touches[0].clientY))
            : ((t = e.clientX), (s = e.clientY));
          const i = t - this.currentX,
            o = s - this.currentY,
            r = this.currentX - (t - this.initialX),
            a = this.currentY - (s - this.initialY);
          (this.currentX = t - this.initialX),
            (this.currentY = s - this.initialY),
            (i >= 5 || o >= 5 || i <= -5 || o <= -5) &&
              (this.moveBackInScreen(r, a),
              this.gp.addCSSClass(this.moveElement, "drag"),
              (this.moveElement.style.transform = `translate(${this.currentX}px, ${this.currentY}px)`),
              this.dragged ||
                ((this.pointerEventsDefault = this.handle.style.pointerEvents),
                (this.handle.style.pointerEvents = "none")),
              (this.dragged = !0));
        }
      }
      dragEnd() {
        this.dragged &&
          ((this.handle.style.pointerEvents = this.pointerEventsDefault),
          this.handle.focus(),
          (this.dragged = !1)),
          (this.active = !1),
          document.removeEventListener("touchmove", this.dragBound),
          document.removeEventListener("mousemove", this.dragBound),
          document.removeEventListener("touchend", this.dragEndBound),
          document.removeEventListener("mouseup", this.dragEndBound);
      }
    }
    var Kn = function (e, t, s, i) {
      return new (s || (s = Promise))(function (o, r) {
        function a(e) {
          try {
            c(i.next(e));
          } catch (e) {
            r(e);
          }
        }
        function n(e) {
          try {
            c(i.throw(e));
          } catch (e) {
            r(e);
          }
        }
        function c(e) {
          var t;
          e.done
            ? o(e.value)
            : ((t = e.value),
              t instanceof s
                ? t
                : new s(function (e) {
                    e(t);
                  })).then(a, n);
        }
        c((i = i.apply(e, t || [])).next());
      });
    };
    const Xn =
        /\b(?:(?:https?|ftp):\/\/|(www\.))[-a-z0-9+&@#/%?=~_|!:,.;]*[-a-z0-9+&@#/%=~_|]/gim,
      Qn = (e, t, s) => {
        const i = ec(e).replace(b(Xn), nc(s, t)),
          o = wc(i, t);
        return oc(o);
      },
      ec = (e) => {
        let t;
        try {
          t = A(e);
        } catch (t) {
          return e;
        }
        return tc(t), sc(t), O(t.innerHTML);
      },
      tc = (e) => (
        e.querySelectorAll("a").forEach((e) => {
          e.outerHTML = ic(e.outerHTML);
        }),
        e
      ),
      sc = (e) => {
        e.querySelectorAll("*").forEach((e) => {
          if ("A" !== e.tagName) {
            const t = e.attributes;
            for (let e = 0; e < t.length; e++) {
              const s = t[e];
              s.value = ic(s.value);
            }
          }
        });
      },
      ic = (e) => e.replace(/(https?|www)/gim, ac),
      oc = (e) => {
        let t = e;
        return (
          rc.forEach((e, s) => {
            t = t.replace(new RegExp(s, "g"), e);
          }),
          rc.clear(),
          t
        );
      },
      rc = new Map(),
      ac = (e) => {
        const t =
          performance.now().toString(36).replace(".", "_") +
          Math.random().toString(36).substring(2);
        return rc.set(t, e), t;
      },
      nc = (e, t) => (s, i) => {
        if (e) {
          const e = cc(s, t);
          if (e) return e;
        }
        return `<a href="${
          i ? `https://${s}` : s
        }" target="_blank" rel="noreferrer">${s}</a>`;
      },
      cc = (e, t) => {
        let s, i;
        try {
          const t = e.toLowerCase().startsWith("https")
            ? new URL(e)
            : new URL(`https://${e}`);
          s = t.hostname.toLowerCase();
        } catch (e) {
          return i;
        }
        return (
          bc.some((o) => {
            const r = s.includes(o.name);
            if (r) {
              const s = ae();
              "videohub" !== o.name && hc(o.url, e, t, s),
                (i = o.getEmbed(o.getId(e), s, t));
            }
            return r;
          }),
          i
        );
      },
      hc = (e, t, s, i) =>
        Kn(void 0, void 0, void 0, function* () {
          const o = `${e}?url=${t}`;
          try {
            const e = yield fetch(o);
            if (!e.ok) return;
            const t = yield e.json();
            if (null == t ? void 0 : t.html) {
              const e = t.html.replace(
                  "<iframe",
                  `<iframe class="${s}-video-wrapper"`
                ),
                o = document.getElementById(i);
              null == o ||
                o.replaceWith(
                  ((e) => {
                    const t = document.createElement("template");
                    return (t.innerHTML = e.trim()), t.content.firstChild;
                  })(e)
                );
            }
          } catch (e) {}
        }),
      lc =
        /(?:youtu.*be.*)\/(?:watch\?v=|embed\/|v\/|shorts|)(.*?((?=[&#?])|$))/gm,
      pc = /(?:https?:\/\/)?videohub\.oracle\.com\/media\/\S+\/([\w]+)/gim,
      dc = /^(?:https?:\/\/)?(?:www\.)?vimeo\.com\/(\d+)(?:|\/\?)/gim,
      uc =
        /^(?:https?:\/\/)?(?:www\.)?(?:dailymotion\.com\/(?:video|embed)|dai.ly)\/([a-z0-9]+)/gim,
      gc = "allow",
      mc = `${gc}="autoplay *; fullscreen *; encrypted-media *" sandbox="${gc}-downloads ${gc}-forms ${gc}-same-origin ${gc}-scripts ${gc}-top-navigation ${gc}-pointer-lock ${gc}-popups ${gc}-modals ${gc}-orientation-lock ${gc}-popups-to-escape-sandbox ${gc}-presentation ${gc}-top-navigation-by-user-activation" height="auto"`,
      bc = [
        {
          name: "youtu",
          url: "https://www.youtube.com/oembed",
          getEmbed: (e, t, s) =>
            vc(
              `src="https://www.youtube.com/embed/${e}" allow="accelerometer; encrypted-media; gyroscope; picture-in-picture"`,
              t,
              s,
              "youtube"
            ),
          getId: (e) => fc(e, lc),
        },
        {
          name: "videohub",
          url: "",
          getEmbed: (e, t, s) => {
            const i = "flashvars";
            return vc(
              `src="https://cdnapisec.kaltura.com/p/2171811/sp/217181100/embedIframeJs/uiconf_id/35965902/partner_id/2171811?iframeembed=true&playerId=kaltura_player&entry_id=${e}&${i}[streamerType]=auto&amp;${i}[localizationCode]=en&amp;${i}[sideBarContainer.plugin]=true&amp;${i}[sideBarContainer.position]=left&amp;${i}[sideBarContainer.clickToClose]=true&amp;${i}[chapters.plugin]=true&amp;${i}[chapters.layout]=vertical&amp;${i}[chapters.thumbnailRotator]=false&amp;${i}[streamSelector.plugin]=true&amp;${i}[EmbedPlayer.SpinnerTarget]=videoHolder&amp;${i}[dualScreen.plugin]=true&amp;${i}[hotspots.plugin]=1&amp;${i}[Kaltura.addCrossoriginToIframe]=true&amp;&wid=1_yz4xoltb" ${mc}`,
              t,
              s,
              "ovh"
            );
          },
          getId: (e) => fc(e, pc),
        },
        {
          name: "vimeo",
          url: "https://vimeo.com/api/oembed.json",
          getEmbed: (e, t, s) =>
            vc(
              `src="https://player.vimeo.com/video/${e}" allow="fullscreen; picture-in-picture"`,
              t,
              s,
              "vimeo"
            ),
          getId: (e) => fc(e, dc),
        },
        {
          name: "dai",
          url: "https://www.dailymotion.com/services/oembed",
          getEmbed: (e, t, s) =>
            vc(
              `src="https://geo.dailymotion.com/player.html?video=${e}" allow="fullscreen; picture-in-picture; web-share"`,
              t,
              s,
              "dailymotion"
            ),
          getId: (e) => fc(e, uc),
        },
      ],
      fc = (e, t) => {
        let s;
        return (
          e.replace(
            b(t),
            (e, t) => ((null == t ? void 0 : t.length) && (s = t), e)
          ),
          s
        );
      },
      wc = (e, t) => {
        const s = A(e);
        if (!s) return e;
        const i = s.querySelectorAll("video"),
          o = `${t}-video-wrapper`;
        return (
          i.forEach((e) => {
            e.classList.add(o);
          }),
          O(s.innerHTML)
        );
      },
      vc = (e, t, s, i) =>
        `<div class="${s}-${i}-wrapper"><iframe id="${t}" class="${s}-video-wrapper" ${e} allowfullscreen frameborder="0"></iframe></div>`,
      xc = "resize",
      kc = [`nw-${xc}`, `se-${xc}`, `nwse-${xc}`, `w-${xc}`, `e-${xc}`],
      yc = [`ne-${xc}`, `sw-${xc}`, `nesw-${xc}`, `e-${xc}`, `w-${xc}`];
    class zc {
      constructor(e, t, s) {
        (this.Mi = e),
          (this.td = t),
          (this.gp = s),
          (this.sd = 200),
          (this.od = 375),
          (this.rd = !1),
          (this.ad = !1);
      }
      makeWidgetResizable() {
        const e = this.Mi,
          t = this.gp,
          s = t.createDiv(["resizable", `top-${xc}`]);
        s.addEventListener("mousedown", this.nd()), e.appendChild(s);
        const i = t.createDiv(["resizable", `left-${xc}`]);
        i.addEventListener("mousedown", this.hd()), e.appendChild(i);
        const o = t.createDiv(["resizable", `right-${xc}`]);
        o.addEventListener("mousedown", this.hd(!1)), e.appendChild(o);
        const r = t.createDiv(["resizable", `left-${xc}`, "corner"]);
        r.addEventListener("mousedown", this.hd(!0, !0)),
          r.addEventListener("mousedown", this.nd(!0)),
          e.appendChild(r);
        const a = t.createDiv(["resizable", `right-${xc}`, "corner"]);
        a.addEventListener("mousedown", this.hd(!1, !0)),
          a.addEventListener("mousedown", this.nd(!0)),
          e.appendChild(a);
      }
      hd(e = !0, t = !1) {
        const s = this.Mi,
          i = e ? kc : yc;
        let o;
        const r = (r) => {
            const a = parseInt(getComputedStyle(s).maxWidth),
              n = s.offsetWidth;
            let c = o - r.x;
            e || (c = -c);
            const h = n + c;
            if (
              (n < this.od && (this.od = n),
              (o = r.x),
              h <= this.od
                ? (document.body.style.cursor = t
                    ? this.rd
                      ? i[0]
                      : i[2]
                    : i[3])
                : (document.body.style.cursor =
                    h >= a
                      ? t
                        ? this.ad
                          ? i[1]
                          : i[2]
                        : i[4]
                      : t
                      ? i[2]
                      : `col-${xc}`),
              h >= this.od && h <= a)
            ) {
              const e = `${h}px`;
              (s.style.width = e), this.td(e);
            }
            r.preventDefault();
          },
          a = () => {
            document.removeEventListener("mouseup", a, !1),
              document.removeEventListener("mousemove", r, !1),
              document.body.style.removeProperty("cursor");
          };
        return (e) => {
          e.preventDefault(),
            (o = e.x),
            document.addEventListener("mouseup", a, !1),
            document.addEventListener("mousemove", r, !1);
        };
      }
      nd(e = !1) {
        const t = this.Mi;
        let s;
        const i = (i) => {
            const o = s - i.y,
              r = parseInt(getComputedStyle(t).maxHeight),
              a = t.offsetHeight,
              n = a + o;
            a < this.sd && (this.sd = a),
              (s = i.y),
              n <= this.sd
                ? ((this.rd = !0),
                  e || (document.body.style.cursor = `n-${xc}`))
                : n >= r
                ? ((this.ad = !0),
                  e || (document.body.style.cursor = `s-${xc}`))
                : ((this.rd = !1),
                  (this.ad = !1),
                  e || (document.body.style.cursor = `row-${xc}`)),
              n >= this.sd && n <= r && (t.style.height = `${n}px`),
              i.preventDefault();
          },
          o = () => {
            document.removeEventListener("mouseup", o, !1),
              document.removeEventListener("mousemove", i, !1),
              document.body.style.removeProperty("cursor");
          };
        return (e) => {
          e.preventDefault(),
            (s = e.y),
            document.addEventListener("mouseup", o, !1),
            document.addEventListener("mousemove", i, !1);
        };
      }
    }
    const $c = {};
    function Cc(e, t) {
      let s;
      const i = Fn(e);
      let o;
      const r = G();
      let a = !1;
      const n = new qn(i);
      (ar.logLevel = i.isDebugMode ? ar.LOG_LEVEL.DEBUG : ar.LOG_LEVEL.ERROR),
        (ar.appName = i.name),
        (ar.appVersion = mi);
      const c = new ar("main"),
        h = new di({
          URI: i.URI,
          channelId: i.channelId,
          userId: i.userId,
          isTLS: i.enableSecureConnection,
          channel: i.channel,
          enableAttachment: i.enableAttachment,
          enableAttachmentSecurity: i.enableAttachmentSecurity,
          isLongPoll: i.enableLongPolling,
          isTTS: i.enableBotAudioResponse,
          TTSService: i.ttsService,
          tokenGenerator: i.clientAuthEnabled ? t : null,
          recognitionLocale: i.speechLocale,
          retryInterval: i.reconnectInterval,
          retryMaxAttempts: i.reconnectMaxAttempts,
          enableCancelResponse: i.enableCancelResponse,
        });
      if (
        (i.skillVoices &&
          (!i.ttsVoice || (Array.isArray(i.ttsVoice) && !i.ttsVoice.length)) &&
          (i.ttsVoice = i.skillVoices),
        i.enableBotAudioResponse)
      )
        try {
          i.ttsVoice && h.setTTSVoice(i.ttsVoice);
        } catch (e) {
          c.error("Failed to initialize TTS");
        }
      const l = Object.values(we),
        d = (e, ...t) => {
          1 === t.length
            ? c.error(
                `Parameter ${t} was not passed for ${e} call. No action processed.`
              )
            : c.error(
                `Parameters ${t.join(
                  ", "
                )} were not passed for ${e} call. No action processed.`
              );
        },
        u = (e) => {
          r.trigger(ui.MESSAGE_SENT, e), r.trigger(ui.MESSAGE, e);
        },
        m = (e) => {
          r.trigger(ui.MESSAGE_RECEIVED, e), r.trigger(ui.MESSAGE, e);
        },
        b = (e) => {
          r.trigger(ui.NETWORK, e);
        },
        f = () => {
          (s = new ua(h, i, {
            connect: this.connect.bind(this),
            openChat: this.openChat.bind(this),
            closeChat: this.closeChat.bind(this),
            handleSessionEnd: v.bind(this),
            receivedMessage: m.bind(this),
            sentMessage: u.bind(this),
            getUnreadMessagesCount: this.getUnreadMessagesCount.bind(this),
            onConnectionStatusChange: b.bind(this),
            util: n,
            eventDispatcher: r,
          })),
            (s.contextWidgetMap = $c),
            s.render();
        };
      let w = () => {
        r.trigger(ui.READY), (w = () => {});
      };
      (this.configureWidget = (e, t, o = !0) => {
        const a = new fa(i, n, e, t, o, $c, h, s, r);
        return this.isConnected() || this.connect(), ($c[a.threadId] = a), a;
      }),
        (this.updateChatContext = (
          e,
          t,
          s,
          o,
          { event: r, semanticObject: a } = {}
        ) => (
          e || d("updateChatContext", "appContext"),
          h.updateChatContext(
            e,
            {
              properties: Object.assign(Object.assign({}, Pn(t)), s),
              event: r,
              semanticObject: a,
            },
            o,
            i.sdkMetadata
              ? Object.assign({ version: mi }, i.sdkMetadata)
              : { version: mi }
          )
        )),
        (this.connect = ({ URI: e, channelId: t, userId: o } = {}) => {
          let r;
          return (
            e || t || o
              ? (((e, t, o) => {
                  "string" == typeof e && e.length && (i.URI = e),
                    "string" == typeof t && t.length && (i.channelId = t),
                    "string" == typeof o &&
                      o.length &&
                      ((i.userId = o), s.configureStorage());
                })(e, t, o),
                (r = h.connect(i)))
              : (r = h.connect()),
            r
              .then(
                () => {
                  c.debug("Connection ready");
                },
                () => {
                  c.debug("Connection timeout"), s.showConnectionError();
                }
              )
              .finally(() => {
                w();
              }),
            r
          );
        }),
        (this.disconnect = () => (
          i.enableSpeech && this.stopVoiceRecording(),
          i.enableBotAudioResponse && this.cancelTTS(),
          h.disconnect()
        )),
        (this.isConnected = () => h.isConnected()),
        (this.openChat = () => {
          s.isOpen || (s.showChat(), a && (this.connect(), (a = !1))),
            r.trigger(ui.WIDGET_OPENED);
        }),
        (this.closeChat = () => {
          s.isOpen && s.onClose(), r.trigger(ui.WIDGET_CLOSED);
        }),
        (this.endChat = () => {
          this.isConnected() && s.sendExitEvent();
        }),
        (this.showWidget = () => {
          null == s || s.showWidget();
        }),
        (this.hideWidget = () => {
          null == s || s.hideWidget();
        });
      const v = () => {
        s.isOpen && this.closeChat(),
          this.disconnect(),
          this.clearConversationHistory(),
          (a = !0),
          r.trigger(ui.CHAT_END);
      };
      (this.isChatOpened = () => s.isOpen),
        (this.destroy = () => {
          if ((this.disconnect(), this.closeChat(), s.remove(), document)) {
            const e = s.styleSheet;
            e && e.remove();
          }
          r.trigger(ui.DESTROY), this.off();
          for (const e in this) this[e] && delete this[e];
        }),
        (this.on = (e, t) => {
          switch (e) {
            case ye.TTSStart:
            case ye.TTSStop:
              h.on(e, t);
              break;
            default:
              r.bind(e, t);
          }
        }),
        (this.off = (e, t) => {
          switch (e) {
            case ye.TTSStart:
            case ye.TTSStop:
              h.off(e, t);
              break;
            default:
              r.unbind(e, t);
          }
        }),
        (this.sendAttachment = (e) =>
          e
            ? s.uploadFile(e)
            : (d("sendAttachment", "file"),
              Promise.reject(new Error("Invalid Parameter")))),
        (this.sendMessage = (e, t) =>
          e
            ? s.sendMessage(e, t)
            : (d("sendMessage", "message"),
              Promise.reject(new Error("Invalid Parameter")))),
        (this.sendUserTypingStatus = (e, t) =>
          e
            ? h.sendUserTypingStatus(e, t)
            : (d("sendUserTypingStatus", "status"),
              Promise.reject(new Error("Invalid Parameter")))),
        (this.updateUser = (e) =>
          e
            ? h
                .updateUser(e, { sdkMetadata: { version: mi } })
                .then((e) => u(e))
            : (d("updateUser", "userDetails"),
              Promise.reject(new Error("Invalid Parameter")))),
        (this.setUserAvatar = (e) => {
          e ? s.setUserAvatar(e) : d("setUserAvatar", "userAvatar");
        }),
        (this.setAgentDetails = (e) => {
          e ? s.setAgentDetails(e) : d("setAgentDetails", "agentDetails");
        }),
        (this.getAgentDetails = () => s.getAgentDetails()),
        (this.setSkillVoices = (e) => {
          if (!h.getTTSService()) return Ic();
          let t = [];
          return (
            e &&
            !Array.isArray(e) &&
            "string" == typeof (null == e ? void 0 : e.lang)
              ? (t = [e])
              : Array.isArray(e) && (t = e),
            this.setTTSVoice(t)
          );
        }),
        (this.setTTSService = (e) => {
          const t = h.getTTSService();
          t && t.cancel(),
            "string" == typeof e
              ? h.setTTSService(e)
              : h.setTTSService(
                  (function (e) {
                    return (
                      e &&
                      p(e.speak) &&
                      p(e.cancel) &&
                      p(e.getVoice) &&
                      p(e.getVoices) &&
                      p(e.setVoice)
                    );
                  })(e)
                    ? e
                    : null
                );
          const o = h.getTTSService();
          (i.ttsService = o),
            s && s.refreshTTS(),
            o &&
              ((i.enableBotAudioResponse = !0),
              wn(o, i.ttsVoice).then((e) => {
                e || (i.ttsVoice = []);
                const t = In({
                  hasRecognition: i.enableSpeech,
                  hasSynthesis: i.enableBotAudioResponse,
                  recognitionLocale: i.speechLocale,
                  synthesisLocales: i.ttsVoice,
                });
                t &&
                  o.setVoice(t).catch((e) => {
                    c.error(e);
                  }),
                  (i.ttsVoice = t);
              }));
        }),
        (this.getTTSVoices = () => h.getTTSVoices()),
        (this.setTTSVoice = (e) => {
          const t = h.getTTSService();
          return t
            ? wn(t, i.ttsVoice).then(
                (t) => (
                  (i.ttsVoice = In({
                    hasRecognition: i.enableSpeech,
                    hasSynthesis: i.enableBotAudioResponse,
                    isReset: t,
                    recognitionLocale: i.speechLocale,
                    synthesisLocales: e,
                  })),
                  h.setTTSVoice(e).catch(() => Ic())
                )
              )
            : Ic();
        }),
        (this.getTTSVoice = () => {
          try {
            return h.getTTSVoice();
          } catch (e) {
            throw Error(Sc);
          }
        }),
        (this.speakTTS = (e) => {
          h.speakTTS(e, i.i18n[i.locale]);
        }),
        (this.cancelTTS = () => {
          h.cancelTTS();
        }),
        (this.setPrimaryChatLanguage = (e) => {
          if (null !== e && "string" != typeof e)
            throw Error("Please pass a language string or null as argument");
          this.isConnected()
            ? s.setPrimaryChatLanguage(e)
            : c.error("Not connected. Can not call setPrimaryChatLanguage.");
        }),
        (this.setDelegate = (e) => {
          i.delegate = e;
        }),
        (this.getConversationHistory = () => {
          const e = s.getMessages();
          return {
            messages: e,
            messagesCount: e.length,
            unreadCount: this.getUnreadMessagesCount(),
            userId: i.userId,
          };
        }),
        (this.clearConversationHistory = (e, t = !0) => {
          e && "string" != typeof e
            ? c.error(
                "Argument passed in clearConversationHistory() is not of type string. Returning without execution."
              )
            : ((e && 0 !== e.length) || (e = i.userId),
              t && e === i.userId
                ? s.clearConversationHistory()
                : s.clearMessages(e, mr.LOCAL));
        }),
        (this.clearAllConversationsHistory = (e = !0) => {
          s.clearAllMessage(), e && s.clearConversationHistory();
        }),
        (this.getSuggestions = (e) =>
          i.enableAutocomplete
            ? e
              ? "string" != typeof e && "number" != typeof e
                ? Promise.reject(
                    "Invalid query parameter type passed for the getSuggestions call."
                  )
                : s.getSuggestions(e)
              : Promise.reject(
                  "No query parameter passed for the getSuggestions call."
                )
            : Promise.reject("Autocomplete suggestions not enabled.")),
        (this.startVoiceRecording = (e, t) =>
          i.enableSpeech
            ? h.startRecognition({
                onRecognitionText: (t) => {
                  null == e || e(t.message);
                },
                onVisualData: null == t ? void 0 : t.onAnalyserFrequencies,
              })
            : Promise.reject(
                new Error(
                  "Speech-to-text feature is not enabled. Initialize the widget with enableSpeech: true to use the service."
                )
              )),
        (this.stopVoiceRecording = () => {
          if (!i.enableSpeech)
            throw new Error(
              "Speech-to-text feature is not enabled. Speech recognition service is not running."
            );
          return h.stopRecognition();
        }),
        (this.setSpeechLocale = (e) => {
          if (!i.enableSpeech) return !1;
          e = e.toLowerCase();
          const t = l.includes(e);
          if (
            ((i.speechLocale = e),
            h.setRecognitionLocale(e),
            s.setVoiceRecognitionService(t),
            t && i.enableBotAudioResponse)
          ) {
            const e = In({
              hasRecognition: i.enableSpeech,
              hasSynthesis: i.enableBotAudioResponse,
              recognitionLocale: i.speechLocale,
              synthesisLocales: i.ttsVoice,
            });
            e !== i.ttsVoice &&
              ((i.ttsVoice = e), e.length && h.setTTSVoice(e));
          }
          return t;
        }),
        (this.getUnreadMessagesCount = () => {
          if (i.enableHeadless) return 0;
          const e = s.getUnreadMsgsCount();
          return e !== o && ((o = e), r.trigger(ui.UNREAD, e)), e;
        }),
        (this.setAllMessagesAsRead = () => {
          i.enableHeadless ||
            (this.getUnreadMessagesCount(), s.updateNotificationBadge(0));
        }),
        (this.showTypingIndicator = () => {
          if (!i.showTypingIndicator)
            throw new Error("Typing indicator is configured not to be shown.");
          if (i.enableHeadless)
            throw new Error(
              "Typing indicator cannot be shown in headless mode."
            );
          this.isConnected() && s.showTypingIndicator();
        }),
        (this.setWebViewConfig = (e) => {
          if (i.enableHeadless)
            throw new Error("WebView cannot be configured in headless mode.");
          s.refreshWebView(e);
        }),
        (this.setUserInputMessage = (e) => {
          if (i.enableHeadless)
            throw new Error("User input cannot be set in headless mode.");
          s.setUserInputMessage(e);
        }),
        (this.setUserInputPlaceholder = (e) => {
          if (i.enableHeadless)
            throw new Error("Placeholder cannot be set in headless mode.");
          e
            ? s.setUserInputPlaceholder(e)
            : d("setUserInputPlaceholder", "placeholder text");
        }),
        (this.setHeight = (e) => {
          e ? null == s || s.setHeight(e) : d("setHeight", "height");
        }),
        (this.setWidth = (e) => {
          e ? null == s || s.setWidth(e) : d("setWidth", "width");
        }),
        (this.setSize = (e, t) => {
          e || t
            ? null == s || s.setSize(e, t)
            : d("setSize", "width", "height");
        }),
        (this.setMessagePadding = (e) => {
          e
            ? null == s || s.setMessagePadding(e)
            : d("setMessagePadding", "padding");
        }),
        (this.setChatBubbleIconHeight = (e) => {
          e
            ? null == s || s.setChatBubbleIconHeight(e)
            : d("setChatBubbleIconHeight", "height");
        }),
        (this.setChatBubbleIconWidth = (e) => {
          e
            ? null == s || s.setChatBubbleIconWidth(e)
            : d("setChatBubbleIconWidth", "width");
        }),
        (this.setChatBubbleIconSize = (e, t) => {
          e || !t
            ? null == s || s.setChatBubbleIconSize(e, t)
            : d("setChatBubbleIconSize", "width", "height");
        }),
        (this.setFont = (e) => {
          e ? (n.updateCSSVar("font", e), (i.font = e)) : d("setFont", "font");
        }),
        (this.setFontFamily = (e) => {
          e
            ? (n.updateCSSVar("font-family", e), (i.fontFamily = e))
            : d("setFontFamily", "fontFamily");
        }),
        (this.setFontSize = (e) => {
          e ? n.updateCSSVar("font-size", e) : d("setFontSize", "fontSize");
        }),
        (this.setTextColor = (e) => {
          e
            ? (n.updateCSSVar("--color-bot-text", e),
              n.updateCSSVar("--color-user-text", e))
            : d("setTextColor", "color");
        }),
        (this.setTextColorLight = (e) => {
          e
            ? (n.updateCSSVar("--color-text-light", e),
              (i.colors.textLight = e))
            : d("setTextColorLight", "color");
        }),
        c.debug("onLoad", "load chat widget"),
        f(),
        g(this);
      const x = window;
      x && "function" == typeof x.define && x.define.amd && (x.WebSDK = Cc);
    }
    const Sc = "Text-to-speech is not available.";
    function Ic() {
      return (e = Sc), Promise.reject(Error(e));
    }
    return (
      (Cc.EVENT = ui),
      (Cc.SPEECH_LOCALE = we),
      (Cc.THEME = br),
      (Cc.TTS = li),
      (Cc.Version = mi),
      u(Cc),
      (t = t.default)
    );
  })()
);
