from clinfail.probes.anchoring import AnchoringProbe
from clinfail.probes.med_override import MedOverrideProbe
from clinfail.probes.med_status import MedStatusProbe

# the "probe" field of an experiment config picks one of these
PROBES = {
    "anchoring": AnchoringProbe,
    "med_override": MedOverrideProbe,
    "med_status": MedStatusProbe,
}
