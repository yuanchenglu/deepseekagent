import { useState, useMemo, type FormEvent } from "react";
import { Eye, EyeOff, LogIn, UserPlus, Smartphone, Mail, User, Shield } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/hooks/useAuth";
import { useI18n } from "@/i18n";

type Mode = "login" | "register";
type LoginMethod = "phone" | "email" | "username";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PHONE_RE = /^1\d{10}$/;

function usePasswordStrength(pw: string) {
  return useMemo(() => {
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[a-z]/.test(pw) && /[A-Z]/.test(pw)) score++;
    if (/\d/.test(pw)) score++;
    if (/[^a-zA-Z0-9]/.test(pw)) score++;
    const labels = ["weak", "fair", "good", "strong"] as const;
    const label = score <= 1 ? labels[0] : score <= 2 ? labels[1] : score <= 3 ? labels[2] : labels[3];
    return { score: Math.min(score, 4), label, valid: score >= 2 };
  }, [pw]);
}

function PasswordStrengthIndicator({ password, t }: { password: string; t: (key: string) => any }) {
  const strength = usePasswordStrength(password);
  if (!password) return null;

  const barColors = ["bg-red-500", "bg-orange-400", "bg-yellow-400", "bg-green-500"];
  const labelMap: Record<string, string> = {
    weak: t.auth.strengthWeak,
    fair: t.auth.strengthFair,
    good: t.auth.strengthGood,
    strong: t.auth.strengthStrong,
  };

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <span className="font-display text-[0.65rem] tracking-[0.1em] uppercase text-muted-foreground">
          {t.auth.passwordStrength}
        </span>
        <span className={`font-display text-[0.65rem] tracking-[0.1em] uppercase ${
          strength.score <= 1 ? "text-red-500" : strength.score <= 2 ? "text-orange-400" : "text-green-500"
        }`}>
          {labelMap[strength.label]}
        </span>
      </div>
      <div className="flex gap-0.5">
        {[0, 1, 2, 3].map((i) => (
          <div
            key={i}
            className={`h-1 flex-1 rounded-full transition-colors ${
              i < strength.score ? barColors[Math.min(strength.score - 1, 3)] : "bg-muted"
            }`}
          />
        ))}
      </div>
      {strength.score < 3 && (
        <p className="font-display text-[0.6rem] text-muted-foreground/60">{t.auth.strengthHint}</p>
      )}
    </div>
  );
}

const LOGIN_METHODS: { key: LoginMethod; icon: typeof Smartphone }[] = [
  { key: "phone", icon: Smartphone },
  { key: "email", icon: Mail },
  { key: "username", icon: User },
];

export default function AuthPage() {
  const { t } = useI18n();
  const { login, register, hasUsers } = useAuth();

  const [mode, setMode] = useState<Mode>(hasUsers ? "login" : "register");
  const [loginMethod, setLoginMethod] = useState<LoginMethod>("phone");
  const [loginInput, setLoginInput] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const validateLogin = (): string | null => {
    const val = loginInput.trim();
    if (!val) return t.auth.loginFailed;
    if (loginMethod === "phone" && !PHONE_RE.test(val)) return t.auth.phoneInvalid;
    if (loginMethod === "email" && !EMAIL_RE.test(val)) return t.auth.emailInvalid;
    if (loginMethod === "username" && val.length < 2) return t.auth.usernameMin;
    if (password.length < 6) return t.auth.passwordMin;
    return null;
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (mode === "login") {
      const validationError = validateLogin();
      if (validationError) {
        setError(validationError);
        return;
      }

      setSubmitting(true);
      try {
        const errMsg = await login(loginInput.trim(), password);
        if (errMsg) setError(errMsg);
      } catch {
        setError("Network error");
      } finally {
        setSubmitting(false);
      }
    } else {
      const u = username.trim();
      const e = email.trim();
      const p = phone.trim();

      if (u.length < 2) {
        setError(t.auth.usernameMin);
        return;
      }
      if (password.length < 6) {
        setError(t.auth.passwordMin);
        return;
      }
      if (password !== confirmPassword) {
        setError(t.auth.passwordMismatch);
        return;
      }
      if (e && !EMAIL_RE.test(e)) {
        setError(t.auth.emailInvalid);
        return;
      }
      if (p && !PHONE_RE.test(p)) {
        setError(t.auth.phoneInvalid);
        return;
      }

      setSubmitting(true);
      try {
        const errMsg = await register(u, password, e || undefined, p || undefined);
        if (errMsg) setError(errMsg);
      } catch {
        setError("Network error");
      } finally {
        setSubmitting(false);
      }
    }
  };

  const switchMode = () => {
    setMode(mode === "login" ? "register" : "login");
    setError(null);
    setConfirmPassword("");
    if (mode === "register") {
      setLoginInput("");
    }
  };

  const isRegister = mode === "register";

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <CardContent className="p-6 sm:p-8">
          <div className="mb-6 text-center">
            <div className="mb-3 flex justify-center">
              <div className="flex h-12 w-12 items-center justify-center border border-border bg-foreground/5">
                {isRegister ? (
                  <UserPlus className="h-5 w-5 text-foreground/70" />
                ) : (
                  <LogIn className="h-5 w-5 text-foreground/70" />
                )}
              </div>
            </div>
            <h1 className="font-expanded text-sm font-bold tracking-[0.08em] uppercase blend-lighter">
              {isRegister ? t.auth.registerTitle : t.auth.loginTitle}
            </h1>
            <p className="mt-1.5 font-display text-xs text-muted-foreground">
              {isRegister ? t.auth.registerSubtitle : t.auth.loginSubtitle}
            </p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            {isRegister ? (
              <>
                <div>
                  <label className="mb-1.5 block font-display text-[0.7rem] tracking-[0.12em] uppercase text-muted-foreground">
                    {t.auth.username}
                  </label>
                  <Input
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    autoComplete="username"
                    autoFocus
                  />
                </div>

                <div>
                  <label className="mb-1.5 block font-display text-[0.7rem] tracking-[0.12em] uppercase text-muted-foreground">
                    {t.auth.email} <span className="text-muted-foreground/50">({t.common.optional})</span>
                  </label>
                  <Input
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder={t.auth.emailPlaceholder}
                    autoComplete="email"
                  />
                </div>

                <div>
                  <label className="mb-1.5 block font-display text-[0.7rem] tracking-[0.12em] uppercase text-muted-foreground">
                    {t.auth.phone} <span className="text-muted-foreground/50">({t.common.optional})</span>
                  </label>
                  <Input
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder={t.auth.phonePlaceholder}
                    autoComplete="tel"
                  />
                </div>
              </>
            ) : (
              <>
                <Tabs defaultValue={loginMethod} className="w-full">
                  {(active, setActive) => (
                    <>
                      <TabsList>
                        {LOGIN_METHODS.map(({ key, icon: Icon }) => (
                          <TabsTrigger
                            key={key}
                            active={active === key}
                            value={key}
                            onClick={() => {
                              setActive(key);
                              setLoginMethod(key);
                              setError(null);
                            }}
                          >
                            <Icon className="mr-1 h-3.5 w-3.5" />
                            {key === "phone"
                              ? t.auth.phone
                              : key === "email"
                                ? t.auth.email
                                : t.auth.username}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                      <div className="mt-3">
                        <label className="mb-1.5 block font-display text-[0.7rem] tracking-[0.12em] uppercase text-muted-foreground">
                          {loginMethod === "phone"
                            ? t.auth.phone
                            : loginMethod === "email"
                              ? t.auth.email
                              : t.auth.username}
                        </label>
                        <Input
                          value={loginInput}
                          onChange={(e) => setLoginInput(e.target.value)}
                          placeholder={
                            loginMethod === "phone"
                              ? t.auth.phonePlaceholder
                              : loginMethod === "email"
                                ? t.auth.emailPlaceholder
                                : t.auth.loginPlaceholder
                          }
                          inputMode={
                            loginMethod === "phone"
                              ? "tel"
                              : loginMethod === "email"
                                ? "email"
                                : "text"
                          }
                          autoComplete={
                            loginMethod === "phone"
                              ? "tel"
                              : loginMethod === "email"
                                ? "email"
                                : "username"
                          }
                          autoFocus
                        />
                      </div>
                    </>
                  )}
                </Tabs>
              </>
            )}

            <div>
              <label className="mb-1.5 block font-display text-[0.7rem] tracking-[0.12em] uppercase text-muted-foreground">
                {t.auth.password}
              </label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete={isRegister ? "new-password" : "current-password"}
                  className="pr-9"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground cursor-pointer"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {isRegister && (
              <>
                <PasswordStrengthIndicator password={password} t={t} />
                <div>
                  <label className="mb-1.5 block font-display text-[0.7rem] tracking-[0.12em] uppercase text-muted-foreground">
                    {t.auth.confirmPassword}
                  </label>
                  <Input
                    type={showPassword ? "text" : "password"}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    autoComplete="new-password"
                  />
                </div>
              </>
            )}

            {error && (
              <div className="rounded border border-destructive/30 bg-destructive/10 px-3 py-2 font-display text-xs text-destructive">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting
                ? t.auth.configuring
                : isRegister
                  ? t.auth.createAccount
                  : t.auth.signIn}
            </Button>
          </form>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={switchMode}
              className="font-display text-xs tracking-[0.08em] text-muted-foreground underline-offset-4 hover:text-foreground hover:underline cursor-pointer"
            >
              {isRegister ? t.auth.alreadyHaveAccount : t.auth.noAccount}
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
