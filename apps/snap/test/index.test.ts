import { installSnap } from "@metamask/snaps-jest";

describe("Signature Decoder v2 Snap", () => {
  it("installs", async () => {
    const { request } = await installSnap();
    expect(typeof request).toBe("function");
  });
});
