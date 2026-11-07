import * as Dialog from "@radix-ui/react-dialog";
import {
  ArrowLeft,
  ArrowRight,
  Bookmark,
  Check,
  ChevronRight,
  CircleHelp,
  FolderHeart,
  Image,
  Leaf,
  LoaderCircle,
  Menu,
  Plus,
  Ruler,
  Search,
  Settings2,
  Shirt,
  ShoppingBag,
  Trash2,
  X,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { api, sourceName } from "./api";
import { BriefForm } from "./components/BriefForm";
import { FitForm } from "./components/FitForm";
import { LookGallery } from "./components/LookGallery";
import { Offers } from "./components/Offers";
import { Preview } from "./components/Preview";
import { ShoppingList } from "./components/ShoppingList";
import type { Config, Garment, Project, Sizes, Stage } from "./types";

const stages: { id: Stage; label: string; icon: typeof Shirt }[] = [
  { id: "brief", label: "Your direction", icon: Shirt },
  { id: "looks", label: "The lookbook", icon: Image },
  { id: "fit", label: "Your fit", icon: Ruler },
  { id: "list", label: "The pieces", icon: Bookmark },
  { id: "offers", label: "The finds", icon: Search },
  { id: "preview", label: "Your outfit", icon: ShoppingBag },
];

function stageFor(project: Project): Stage {
  if (project.preview) return "preview";
  if (project.search_links.length || project.job?.kind === "search")
    return "offers";
  if (project.garments.length) return "list";
  if (project.selected.length) return "fit";
  if (project.looks.length || project.job?.kind === "looks") return "looks";
  return "brief";
}

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [config, setConfig] = useState<Config | null>(null);
  const [stage, setStage] = useState<Stage>("brief");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [chosen, setChosen] = useState<string[]>([]);
  const activeJob =
    project?.job && ["running", "queued"].includes(project.job.status);
  const busy = pending || !!activeJob;

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" });
  }, [stage]);

  useEffect(() => {
    let mounted = true;
    Promise.all([api<Config>("/config"), api<Project[]>("/projects")])
      .then(([settings, saved]) => {
        if (!mounted) return;
        setConfig(settings);
        setProjects(saved);
        const previous = saved.find(
          (item) => item.id === localStorage.getItem("stylemax_project"),
        );
        if (previous) {
          setProject(previous);
          setStage(stageFor(previous));
        }
      })
      .catch(() => {
        if (mounted)
          setError(
            "The studio can’t reach its server. Start the Style-Max backend, then reload this page.",
          );
      });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (project) localStorage.setItem("stylemax_project", project.id);
  }, [project]);
  useEffect(() => {
    if (project?.job?.status === "completed" && project.job.kind === "preview")
      setStage("preview");
    if (project?.job?.status === "completed" && project.job.kind === "search")
      setChosen(project.basket?.offer_ids || []);
  }, [project]);

  useEffect(() => {
    if (!project || !activeJob) return;
    let alive = true;
    const interval = setInterval(() => {
      api<Project>(`/projects/${project.id}`)
        .then((next) => {
          if (alive) setProject(next);
        })
        .catch(() => {
          if (alive)
            setError(
              "Connection interrupted. Your project is saved. Reload to reconnect.",
            );
        });
    }, 2000);
    return () => {
      alive = false;
      clearInterval(interval);
    };
  }, [project?.id, activeJob]); // eslint-disable-line react-hooks/exhaustive-deps

  const refreshLibrary = useCallback(
    async () => setProjects(await api<Project[]>("/projects")),
    [],
  );
  async function run(action: () => Promise<void>) {
    setPending(true);
    setError("");
    try {
      await action();
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Something went wrong. Please retry.",
      );
    } finally {
      setPending(false);
    }
  }
  async function start(
    vibe: string,
    budget: number,
    photos: File[],
    demo: boolean,
  ) {
    await run(async () => {
      let next = await api<Project>("/projects", "POST", {
        vibe,
        budget,
        demo,
      });
      setProject(next);
      if (!demo) {
        const form = new FormData();
        photos.forEach((photo) => form.append("photos", photo));
        next = await api<Project>(`/projects/${next.id}/photos`, "POST", form);
        setProject(next);
        next = await api<Project>(`/projects/${next.id}/generate`, "POST");
      }
      setProject(next);
      setStage("looks");
      await refreshLibrary();
    });
  }
  function selectLook(id: string) {
    setProject((previous) =>
      previous
        ? {
            ...previous,
            selected: previous.selected.includes(id)
              ? previous.selected.filter((value) => value !== id)
              : [...previous.selected, id],
          }
        : previous,
    );
  }
  function continueLooks() {
    if (!project) return;
    void run(async () => {
      setProject(
        await api<Project>(`/projects/${project.id}/selection`, "PUT", {
          look_ids: project.selected,
        }),
      );
      setStage("fit");
    });
  }
  function submitSizes(sizes: Sizes) {
    if (!project) return;
    void run(async () => {
      setProject(
        await api<Project>(`/projects/${project.id}/shopping-list`, "PUT", {
          sizes,
        }),
      );
      setStage("list");
    });
  }
  function findOffers(garments?: Garment[], budget?: number) {
    if (!project) return;
    void run(async () => {
      if (garments)
        await api(`/projects/${project.id}/shopping-list`, "PUT", {
          sizes: project.sizes,
          garments,
          budget,
        });
      setProject(await api<Project>(`/projects/${project.id}/search`, "POST"));
      setStage("offers");
    });
  }
  function chooseOffer(id: string) {
    const item = project?.offers.find((offer) => offer.id === id);
    setChosen((current) =>
      current.includes(id)
        ? current.filter((value) => value !== id)
        : [
            ...current.filter(
              (value) =>
                project?.offers.find((offer) => offer.id === value)
                  ?.garment_id !== item?.garment_id,
            ),
            id,
          ],
    );
  }
  function makePreview() {
    if (!project) return;
    void run(async () => {
      setProject(
        await api<Project>(`/projects/${project.id}/preview`, "POST", {
          offer_ids: chosen,
        }),
      );
    });
  }
  function canVisit(value: Stage) {
    if (value === "brief") return true;
    if (!project) return false;
    return value === "looks"
      ? !!project.looks.length
      : value === "fit"
        ? !!project.selected.length
        : value === "list"
          ? !!project.garments.length
          : value === "offers"
            ? !!project.search_links.length
            : !!project.preview;
  }
  function navigate(value: Stage) {
    if (value === "fit" && stage === "looks") {
      continueLooks();
      return;
    }
    setStage(value);
    setMobileOpen(false);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function newProject() {
    setProject(null);
    setStage("brief");
    setError("");
    setMobileOpen(false);
    localStorage.removeItem("stylemax_project");
  }
  function openProject(item: Project) {
    setProject(item);
    setStage(stageFor(item));
    setLibraryOpen(false);
    setChosen(item.basket?.offer_ids || []);
  }
  function deleteProject(id: string) {
    void run(async () => {
      await api(`/projects/${id}`, "DELETE");
      if (project?.id === id) newProject();
      await refreshLibrary();
    });
  }

  return (
    <div className="app-shell">
      {mobileOpen && (
        <button
          className="mobile-scrim"
          aria-label="Close navigation"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <aside className={`sidebar ${mobileOpen ? "mobile-open" : ""}`}>
        <button
          className="brand"
          onClick={newProject}
          aria-label="Style Max home"
        >
          <span className="brand-mark">
            <Shirt size={22} strokeWidth={1.4} />
          </span>
          <span>
            style<span className="brand-max">max</span>
            <span className="brand-period">.</span>
          </span>
        </button>
        <span className="sidebar-caption">Your personal style studio</span>
        <button className="new-edit" onClick={newProject} disabled={busy}>
          <Plus size={17} /> A new direction <span>↗</span>
        </button>
        <p className="nav-label">The process</p>
        <nav aria-label="Styling process">
          {stages.map(({ id, label, icon: Icon }, index) => (
            <button
              key={id}
              disabled={!canVisit(id) || busy}
              className={`nav-item ${stage === id ? "active" : ""}`}
              onClick={() => navigate(id)}
            >
              <Icon size={17} strokeWidth={1.6} />
              <span>{label}</span>
              {stages.findIndex((item) => item.id === stage) > index &&
              canVisit(id) ? (
                <Check className="nav-trailing" size={13} />
              ) : (
                <span className="nav-trailing nav-index">0{index + 1}</span>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-saved">
          <p className="nav-label">Your collection</p>
          <button
            className="nav-item"
            onClick={() => {
              void refreshLibrary();
              setLibraryOpen(true);
            }}
          >
            <FolderHeart size={17} />
            <span>Saved projects</span>
            <span className="count-pill">{projects.length}</span>
          </button>
        </div>
        <div className="sidebar-bottom">
          <div className="second-life">
            <Leaf size={18} strokeWidth={1.4} />
            <p>
              Good clothes.
              <br />
              <strong>Another chapter.</strong>
            </p>
          </div>
          <button className="nav-item" onClick={() => setSettingsOpen(true)}>
            <CircleHelp size={17} />
            <span>Setup & connections</span>
            <ArrowRight size={14} />
          </button>
          <div className="studio-profile">
            <span className="profile-avatar">Y</span>
            <div>
              <strong>Your private studio</strong>
              <span>Wear it your way.</span>
            </div>
            <button
              className="icon-button"
              aria-label="Open settings"
              onClick={() => setSettingsOpen(true)}
            >
              <Settings2 size={15} />
            </button>
          </div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div>
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMobileOpen(true)}
            >
              <Menu size={20} />
            </button>
            <span className="topbar-home">Your studio</span>
            <ChevronRight size={13} />
            <span>{stages.find((item) => item.id === stage)?.label}</span>
          </div>
          <div>
            <span className="private-label">
              <span />
              Private by design
            </span>
            <button
              className="topbar-library"
              aria-label="Open saved projects"
              onClick={() => {
                void refreshLibrary();
                setLibraryOpen(true);
              }}
            >
              <Bookmark size={16} />
            </button>
          </div>
        </header>
        <main id="main-content">
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <button
                className="icon-button"
                aria-label="Dismiss error"
                onClick={() => setError("")}
              >
                <X size={16} />
              </button>
            </div>
          )}
          {stage !== "brief" && (
            <button
              className="back-link"
              disabled={busy}
              onClick={() =>
                setStage(
                  stages[
                    Math.max(
                      0,
                      stages.findIndex((item) => item.id === stage) - 1,
                    )
                  ].id,
                )
              }
            >
              <ArrowLeft size={13} /> Back to{" "}
              {stages[
                Math.max(0, stages.findIndex((item) => item.id === stage) - 1)
              ].label.toLowerCase()}
            </button>
          )}
          {activeJob && (
            <div className="job-progress" role="status">
              <LoaderCircle size={18} className="spin" />
              <div>
                <strong>
                  {project.job?.kind === "looks"
                    ? "Your lookbook is taking shape"
                    : project.job?.kind === "search"
                      ? "Looking for your pieces"
                      : "Putting your outfit together"}
                </strong>
                <span>
                  {project.job?.kind === "looks"
                    ? `${project.job.completed} of 10 looks ready. You can browse as they arrive.`
                    : "You can leave this tab open. We’ll keep your progress saved."}
                </span>
              </div>
              <div className="progress-track">
                <span
                  style={{
                    width: `${Math.max(5, (project.job!.completed / project.job!.total) * 100)}%`,
                  }}
                />
              </div>
            </div>
          )}
          {stage === "brief" && (
            <BriefForm
              busy={busy}
              config={config}
              onStart={(...args) => void start(...args)}
            />
          )}
          {project && stage === "looks" && (
            <LookGallery
              project={project}
              onToggle={selectLook}
              onContinue={continueLooks}
              onRetry={() =>
                void run(async () => {
                  setProject(
                    await api<Project>(
                      `/projects/${project.id}/generate`,
                      "POST",
                    ),
                  );
                })
              }
              busy={busy}
            />
          )}
          {project && stage === "fit" && (
            <FitForm
              key={project.id}
              project={project}
              busy={busy}
              onSubmit={submitSizes}
            />
          )}
          {project && stage === "list" && (
            <ShoppingList
              key={project.updated_at || project.id}
              project={project}
              busy={busy}
              onSearch={findOffers}
            />
          )}
          {project && stage === "offers" && (
            <Offers
              project={project}
              busy={busy}
              chosen={chosen}
              onChoose={chooseOffer}
              onSearch={() => findOffers()}
              onPreview={makePreview}
            />
          )}
          {project && stage === "preview" && (
            <Preview project={project} onBack={() => setStage("offers")} />
          )}
          {project?.error && stage !== "looks" && (
            <div className="inline-error" role="alert">
              {project.error}
            </div>
          )}
          {pending && (
            <div className="saving-indicator" role="status">
              <LoaderCircle size={14} className="spin" /> Saving your edit…
            </div>
          )}
        </main>
        <footer className="app-footer">
          <span>
            Style Max <span>—</span> Less scrolling. More you.
          </span>
          <span>Thoughtfully found. Pre-loved first.</span>
        </footer>
      </div>
      <Dialog.Root open={settingsOpen} onOpenChange={setSettingsOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content className="dialog-content">
            <Dialog.Title>Make the studio yours.</Dialog.Title>
            <Dialog.Description>
              Connect local AI services and marketplaces to turn the demo into
              your personal styling studio.
            </Dialog.Description>
            <Dialog.Close
              className="dialog-close icon-button"
              aria-label="Close settings"
            >
              <X size={18} />
            </Dialog.Close>
            <div className="connection-list">
              <div>
                <span
                  className={`status-dot ${config?.image_worker_configured ? "connected" : ""}`}
                />
                <div>
                  <strong>Image worker</strong>
                  <p>
                    {config?.image_worker_configured
                      ? "Configured · availability checked on generation"
                      : "Not connected · demo available"}
                  </p>
                </div>
              </div>
              <div>
                <span className="status-dot" />
                <div>
                  <strong>AI stylist · {config?.planner || "Ollama"}</strong>
                  <p>
                    Local language model · availability checked on generation
                  </p>
                </div>
              </div>
              {["ebay", "vinted", "kleinanzeigen"].map((source) => (
                <div key={source}>
                  <span
                    className={`status-dot ${config?.sources[source] ? "connected" : ""}`}
                  />
                  <div>
                    <strong>{sourceName(source)}</strong>
                    <p>
                      {config?.sources[source]
                        ? "Enabled · live availability varies"
                        : "Not connected · direct searches available"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            <p className="settings-instructions">
              Configure connections in the server’s <code>.env</code> file and
              restart it. API keys stay on your server. The repository README
              includes Windows, Docker, GPU worker and marketplace setup
              instructions.
            </p>
            <a
              className="button primary full"
              href="https://github.com/kooglersHub/Style-Max#readme"
              target="_blank"
              rel="noopener noreferrer"
            >
              Open the setup guide <ArrowRight size={16} />
            </a>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
      <Dialog.Root open={libraryOpen} onOpenChange={setLibraryOpen}>
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content className="dialog-content library-dialog">
            <Dialog.Title>Your saved directions.</Dialog.Title>
            <Dialog.Description>
              Projects stay in this browser’s private studio. Deleting a project
              removes its photos and generated images.
            </Dialog.Description>
            <Dialog.Close
              className="dialog-close icon-button"
              aria-label="Close saved projects"
            >
              <X size={18} />
            </Dialog.Close>
            <div className="project-library">
              {projects.length ? (
                projects.map((item) => (
                  <div className="library-row" key={item.id}>
                    <button onClick={() => openProject(item)}>
                      <span>
                        {item.demo ? "Demo" : "Personal"} ·{" "}
                        {new Date(item.created_at).toLocaleDateString()}
                      </span>
                      <strong>{item.vibe}</strong>
                      <small>
                        {item.looks.length} looks · {item.selected.length} saved{" "}
                        <ArrowRight size={12} />
                      </small>
                    </button>
                    <button
                      className="icon-button"
                      aria-label={`Delete project ${item.vibe}`}
                      disabled={busy}
                      onClick={() => deleteProject(item.id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <FolderHeart size={30} />
                  <h3>A fresh page.</h3>
                  <p>Your first style direction will appear here.</p>
                </div>
              )}
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </div>
  );
}
